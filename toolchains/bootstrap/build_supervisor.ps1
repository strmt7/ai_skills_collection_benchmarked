param([switch]$Check,[string]$CacheRoot,[string]$OutputDirectory)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$utf8=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=$utf8
$homePath=$PSScriptRoot
$root=[IO.Path]::GetFullPath((Join-Path $homePath '../..'))
function Digest([byte[]]$Bytes) {
    $hash=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}
    finally {$hash.Dispose()}
}
function NativePath([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if($full.StartsWith('\\?\') -or $full.Length -lt 260){return $full}
    if($full.StartsWith('\\')){return '\\?\UNC\'+$full.Substring(2)}
    return '\\?\'+$full
}
function ReadBytes([string]$Path){return ,([IO.File]::ReadAllBytes((NativePath $Path)))}
function WriteJson([string]$Path,$Value){[IO.File]::WriteAllText((NativePath $Path),($Value|ConvertTo-Json -Depth 12).Replace("`r`n","`n")+"`n",$utf8)}
if([string]::IsNullOrEmpty($OutputDirectory)){$OutputDirectory=Join-Path $root ('.venv/supervisor-build/'+[Guid]::NewGuid().ToString('N'))}
$output=[IO.Path]::GetFullPath($OutputDirectory)
if(-not $output.StartsWith(((Join-Path $root '.venv')+'\'),[StringComparison]::OrdinalIgnoreCase) -or [IO.Directory]::Exists((NativePath $output))){throw 'Build output must be a fresh directory in the selected checkout cache'}
# Load the last admitted compiler seed by binary identity only. Source changes
# are the purpose of this maintainer operation; ordinary setup also binds source.
$pinPath=Join-Path $homePath 'supervisor.json'
$pin=[IO.File]::ReadAllText((NativePath $pinPath),$utf8)|ConvertFrom-Json
$libraryPath=Join-Path $homePath 'NativeSupervisor.dll'
$seed=ReadBytes $libraryPath
if($pin.schema_version -ne 1 -or $seed.Length -ne $pin.assembly_bytes -or (Digest $seed) -cne $pin.assembly_sha256){throw 'Restore the tracked native supervisor seed and its pin before rebuilding'}
[void][Reflection.Assembly]::Load($seed)
[void][IO.Directory]::CreateDirectory((NativePath $output))
$environment=New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
foreach($item in [Environment]::GetEnvironmentVariables('Process').GetEnumerator()){$environment.Add([string]$item.Key,[string]$item.Value)}
$temporary=Join-Path $output 'temporary'
[void][IO.Directory]::CreateDirectory((NativePath $temporary))
$environment['TEMP']=$temporary; $environment['TMP']=$temporary
$environment['POWERSHELL_TELEMETRY_OPTOUT']='1'; $environment['POWERSHELL_UPDATECHECK']='Off'
$records=New-Object 'System.Collections.Generic.List[object]'
function Run([string]$Name,[string]$Executable,[string[]]$Arguments) {
    $stdout=Join-Path $output ($Name+'.stdout.native'); $stderr=Join-Path $output ($Name+'.stderr.native')
    $process=[SkillsBootstrap.OwnedProcess]::Run($Executable,$Arguments,$root,$environment,$stdout,$stderr,600,2097152,1073741824,32)
    $records.Add(@{name=$Name;process=$process})
    if($process.exit_code -ne 0 -or $null -ne $process.termination_reason -or $process.active_processes_after_cleanup -ne 0){throw "Native supervisor build step failed: $Name; diagnostics: $output"}
    return [IO.File]::ReadAllText((NativePath $stdout),$utf8)
}
$passed=$false; $failure=$null
try {
    $system=[Environment]::GetFolderPath('System')
    if(-not [Environment]::Is64BitProcess -and [Environment]::Is64BitOperatingSystem){$system=Join-Path ([Environment]::GetFolderPath('Windows')) 'Sysnative'}
    $shell=Join-Path $system 'WindowsPowerShell/v1.0/powershell.exe'
    $arguments=@('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $homePath 'bootstrap.ps1'),'-Root',$root,'-Profile','supervisor-build')
    if(-not [string]::IsNullOrEmpty($CacheRoot)){$arguments+=@('-CacheRoot',$CacheRoot)}
    $inputs=(Run 'provision' $shell $arguments)|ConvertFrom-Json
    $enginePin=[IO.File]::ReadAllText((Join-Path $homePath 'powershell.json'),$utf8)|ConvertFrom-Json
    foreach($name in @('pwsh.exe','Microsoft.CodeAnalysis.dll','Microsoft.CodeAnalysis.CSharp.dll')){
        if((Digest (ReadBytes (Join-Path ([IO.Path]::GetDirectoryName($inputs.engine)) $name))) -cne $enginePin.files.$name.sha256){throw 'Compiler payload differs from its pin'}
    }
    $environment['PSModulePath']=Join-Path ([IO.Path]::GetDirectoryName($inputs.engine)) 'Modules'
    $environment['PSModuleAnalysisCachePath']=Join-Path $output 'module-analysis.cache'
    $source=Join-Path $homePath 'OwnedProcess.cs'
    $sourceDigest=Digest (ReadBytes $source)
    $buildInputs=[ordered]@{}
    foreach($name in @('powershell.json','framework-references.json','CompileSupervisor.ps1','build_supervisor.ps1')){$buildInputs[$name]=Digest (ReadBytes (Join-Path $homePath $name))}
    foreach($label in @('first','second')){
        [void](Run $label $inputs.engine @('-NoLogo','-NoProfile','-NonInteractive','-MTA','-File',(Join-Path $homePath 'CompileSupervisor.ps1'),'-Source',$source,'-References',$inputs.references,'-Output',(Join-Path $output ($label+'.dll'))))
    }
    $first=ReadBytes (Join-Path $output 'first.dll')
    $digest=Digest $first
    if($digest -cne (Digest (ReadBytes (Join-Path $output 'second.dll')))){throw 'Two independent compilations produced different bytes'}
    if($sourceDigest -cne (Digest (ReadBytes $source))){throw 'Supervisor source changed during compilation'}
    foreach($name in $buildInputs.Keys){if($buildInputs[$name] -cne (Digest (ReadBytes (Join-Path $homePath $name)))){throw 'Build inputs changed during compilation'}}
    $generated=[ordered]@{schema_version=1;assembly_bytes=$first.Length;assembly_sha256=$digest;source_sha256=$sourceDigest;build_inputs=$buildInputs}
    if($Check){
        if($pin.assembly_sha256 -cne $digest -or $pin.assembly_bytes -ne $first.Length -or $pin.source_sha256 -cne $sourceDigest -or -not ($pin.psobject.Properties.Name -contains 'build_inputs')){throw 'Generated supervisor or source pin is stale'}
        if(@($pin.build_inputs.psobject.Properties).Count -ne $buildInputs.Count){throw 'Generated supervisor build input set is stale'}
        foreach($name in $buildInputs.Keys){if($pin.build_inputs.$name -cne $buildInputs[$name]){throw 'Generated supervisor build input pin is stale'}}
    }else{
        $pending=Join-Path $homePath ('supervisor-'+[Guid]::NewGuid().ToString('N')+'.tmp')
        try{[IO.File]::WriteAllBytes((NativePath $pending),$first);[IO.File]::Replace((NativePath $pending),(NativePath $libraryPath),[NullString]::Value)}finally{if([IO.File]::Exists((NativePath $pending))){[IO.File]::Delete((NativePath $pending))}}
        WriteJson $pinPath $generated
    }
    $passed=$true
}catch{$failure=$_.Exception.ToString()}
finally{WriteJson (Join-Path $output 'result.json') @{passed=$passed;check_only=[bool]$Check;failure=$failure;controls=$records;model_requests=0;reference_assemblies_executed=$false}}
if(-not $passed){throw $failure}
@{passed=$true;check_only=[bool]$Check;diagnostics=$output}|ConvertTo-Json -Compress
