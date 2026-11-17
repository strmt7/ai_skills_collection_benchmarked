$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$inputArguments=@($args)
$Root=$PSScriptRoot; $CacheRoot=$null; $index=0
$commandMemoryGiB=4; $commandMemorySpecified=$false
$credentialNames=New-Object 'System.Collections.Generic.List[string]'
while($index -lt $inputArguments.Count -and $inputArguments[$index] -in @('--cache-root','--credential-env','--command-memory-gib')) {
    $option=$inputArguments[$index]; $index++
    if($index -ge $inputArguments.Count) { throw "Missing path for $option" }
    if ($option -eq '--cache-root') { $CacheRoot=[string]$inputArguments[$index] }
    elseif ($option -eq '--credential-env') { $credentialNames.Add([string]$inputArguments[$index]) }
    else {
        $memoryText=[string]$inputArguments[$index]
        if ($commandMemorySpecified -or $memoryText -cnotmatch '^(?:[1-9]|[12][0-9]|3[0-2])$') { throw 'Supply --command-memory-gib once with an integer from 1 to 32' }
        $commandMemoryGiB=[int]$memoryText; $commandMemorySpecified=$true
    }
    $index++
}
if ($credentialNames.Count -gt 16) { throw 'Credential environment declaration exceeds its bound' }
$seenCredentials=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($name in $credentialNames) {
    if ($name -cnotmatch '^[A-Za-z_][A-Za-z0-9_]{0,127}$' -or -not $seenCredentials.Add($name)) { throw 'Credential environment names must be valid and distinct' }
}
$Operation='doctor'
if($index -lt $inputArguments.Count) { $Operation=[string]$inputArguments[$index]; $index++ }
if($Operation -notin @('doctor','python','cocoindex','crawl4ai','codex')) { throw 'Use doctor, python, cocoindex, crawl4ai or codex' }
if ($commandMemorySpecified -and $Operation -ne 'python') { throw 'Command memory configuration requires the python operation' }
if ($Operation -in @('doctor','codex') -and $credentialNames.Count -gt 0) { throw 'Credential forwarding requires a development command' }
$CommandArguments=@()
if($index -lt $inputArguments.Count) { $CommandArguments=@($inputArguments[$index..($inputArguments.Count-1)] | ForEach-Object { [string]$_ }) }
if ($Operation -eq 'codex' -and [string]::IsNullOrEmpty($CacheRoot)) { $CacheRoot=Join-Path $Root '.venv/cli' }
$system=[Environment]::GetFolderPath('System')
if (-not [Environment]::Is64BitProcess -and [Environment]::Is64BitOperatingSystem) {
    $system=[IO.Path]::Combine([Environment]::GetFolderPath('Windows'),'Sysnative')
}
$shell=[IO.Path]::Combine($system,'WindowsPowerShell\v1.0\powershell.exe')
if (-not [IO.File]::Exists($shell)) { throw 'Windows PowerShell is unavailable at the native operating-system location' }
$parameters=@('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $Root 'toolchains/bootstrap/bootstrap.ps1'),'-Root',$Root)
if (-not [string]::IsNullOrEmpty($CacheRoot)) { $parameters+=@('-CacheRoot',$CacheRoot) }
if ($commandMemorySpecified) { $parameters+=@('-CommandMemoryGiB',[string]$commandMemoryGiB) }
if ($credentialNames.Count -gt 0) {
    $namesJson=ConvertTo-Json -InputObject @($credentialNames.ToArray()) -Compress
    $parameters+=@('-CredentialEnvironmentBase64',[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($namesJson)))
}
if ($Operation -eq 'codex') {
    if ($CommandArguments.Count -gt 0) { throw 'The codex operation provisions the benchmark CLI; it accepts no execution arguments' }
    $parameters+=@('-Profile','codex')
} elseif ($Operation -in @('python','cocoindex','crawl4ai')) {
    if ($Operation -in @('cocoindex','crawl4ai')) {
        if ($CommandArguments.Count -eq 0) { $CommandArguments=@('check') }
        $CommandArguments=@('tools/_provider_launch.py',$Operation)+$CommandArguments
        $parameters+=@('-Profile','agent-tools')
    }
    if ($CommandArguments.Count -eq 0) { throw 'Supply a Python module, script, code argument or version query' }
    $json=ConvertTo-Json -InputObject @($CommandArguments) -Compress
    $parameters+=@('-CommandBase64',[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json)))
} elseif ($CommandArguments.Count -gt 0) { throw 'The doctor operation accepts no command arguments' }
# Own the first bootstrap process too: an unowned first hop survives abrupt
# termination of this frontend even when its later descendants use jobs.
function Frontend-NativePath([string]$Path) {
    $full=[IO.Path]::GetFullPath($Path)
    if ($full.StartsWith('\\?\')) { return $full }
    if ($full.StartsWith('\\')) { return '\\?\UNC\'+$full.Substring(2) }
    return '\\?\'+$full
}
$bootstrapHome=Join-Path $Root 'toolchains/bootstrap'
$utf8=New-Object Text.UTF8Encoding($false)
$supervisorPin=[IO.File]::ReadAllText((Frontend-NativePath (Join-Path $bootstrapHome 'supervisor.json')),$utf8) | ConvertFrom-Json
$supervisorBytes=[IO.File]::ReadAllBytes((Frontend-NativePath (Join-Path $bootstrapHome 'NativeSupervisor.dll')))
$sourceBytes=[IO.File]::ReadAllBytes((Frontend-NativePath (Join-Path $bootstrapHome 'OwnedProcess.cs')))
$hasher=[Security.Cryptography.SHA256]::Create()
try {
    $assemblyDigest=[BitConverter]::ToString($hasher.ComputeHash($supervisorBytes)).Replace('-','').ToLowerInvariant()
    $sourceDigest=[BitConverter]::ToString($hasher.ComputeHash($sourceBytes)).Replace('-','').ToLowerInvariant()
} finally { $hasher.Dispose() }
if ($supervisorPin.schema_version -ne 1 -or $supervisorBytes.Length -ne $supervisorPin.assembly_bytes -or $assemblyDigest -cne $supervisorPin.assembly_sha256 -or $sourceDigest -cne $supervisorPin.source_sha256) { throw 'The native supervisor differs from its source or binary pin' }
[void][Reflection.Assembly]::Load($supervisorBytes)
$environment=New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($item in [Environment]::GetEnvironmentVariables('Process').GetEnumerator()) {
    $environment.Add([string]$item.Key,[string]$item.Value)
}
$diagnostics=Join-Path ([IO.Path]::GetTempPath()) ('ai-skills-frontend-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory((Frontend-NativePath $diagnostics))
$stdout=Join-Path $diagnostics 'stdout.native'; $stderr=Join-Path $diagnostics 'stderr.native'
$frontendMemoryBytes=[long]([Math]::Max(8,$commandMemoryGiB+4))*1GB
$resources=@{source_root=$Root; memory_limit_bytes=$frontendMemoryBytes; command_memory_limit_bytes=([long]$commandMemoryGiB*1GB); scope='Owned first bootstrap hop; limits are ceilings, not reservations'}
[IO.File]::WriteAllText((Frontend-NativePath (Join-Path $diagnostics 'resources.json')),($resources | ConvertTo-Json),$utf8)
$result=[SkillsBootstrap.OwnedProcess]::Run($shell,[string[]]$parameters,$Root,$environment,$stdout,$stderr,3600,16777216,$frontendMemoryBytes,256)
[IO.File]::WriteAllText((Frontend-NativePath (Join-Path $diagnostics 'process.json')),($result | ConvertTo-Json),$utf8)
foreach ($line in [IO.File]::ReadLines((Frontend-NativePath $stdout),$utf8)) {
    Write-Output -InputObject $line
}
foreach ($line in [IO.File]::ReadLines((Frontend-NativePath $stderr),$utf8)) {
    Write-Error -Message $line -ErrorAction Continue
}
if ($null -ne $result.termination_reason -or $result.active_processes_after_cleanup -ne 0) { throw "Frontend bootstrap did not complete normally; diagnostics: $diagnostics" }
exit $result.exit_code
