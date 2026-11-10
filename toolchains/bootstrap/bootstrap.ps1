param(
    [Parameter(Mandatory=$true)][string]$Root,
    [string]$CacheRoot,
    [ValidateSet('validation','agent-tools','git','codex')][string]$Profile = 'validation',
    [ValidateRange(1,600)][int]$LockTimeoutSeconds = 600,
    [string]$CommandBase64,
    [string]$CredentialEnvironmentBase64
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$utf8 = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
[Console]::Error.Write('')
$rootPath = [IO.Path]::GetFullPath($Root)
if ($rootPath.Length -gt [IO.Path]::GetPathRoot($rootPath).Length) { $rootPath=$rootPath.TrimEnd('\') }
if (-not [IO.File]::Exists((Join-Path $rootPath 'pyproject.toml'))) { throw 'The selected checkout has no project declaration' }
$architecture = $env:PROCESSOR_ARCHITECTURE
if ($env:PROCESSOR_ARCHITEW6432) { $architecture = $env:PROCESSOR_ARCHITEW6432 }
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT -or $architecture -ne 'AMD64') { throw 'This bootstrap target requires Windows x64' }
Add-Type -AssemblyName System.IO.Compression
$bootstrapHome=$PSScriptRoot
$archivePython=$null
. (Join-Path $PSScriptRoot 'ArchiveLayers.ps1')
$manifestPath = Join-Path $PSScriptRoot 'manifest.json'
$manifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
$spec = if ($Profile -in @('git','codex')) { @{python='none'; requirements=@()} } else { $manifest.profiles.$Profile }
if ($Profile -in @('git','codex') -and -not [string]::IsNullOrEmpty($CommandBase64)) { throw 'The selected tool-only profile cannot execute Python commands' }
if (-not [string]::IsNullOrEmpty($CredentialEnvironmentBase64) -and [string]::IsNullOrEmpty($CommandBase64)) { throw 'Credential forwarding requires a development command' }
function Forward-CredentialEnvironment([string]$Encoded,$Variables) {
    if ([string]::IsNullOrEmpty($Encoded)) { return }
    if ($Encoded.Length -gt 8192) { throw 'Credential environment declaration exceeds its bound' }
    $names = ConvertFrom-Json -InputObject ($utf8.GetString([Convert]::FromBase64String($Encoded))) -NoEnumerate
    if ($names -isnot [Array] -or $names.Count -eq 0 -or $names.Count -gt 16) { throw 'Credential environment names must be a bounded nonempty array' }
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in $names) {
        if ($name -isnot [string] -or $name -cnotmatch '^[A-Za-z_][A-Za-z0-9_]{0,127}$' -or -not $seen.Add($name)) { throw 'Credential environment names must be valid and distinct' }
        if ($Variables.ContainsKey($name)) { throw 'Credential forwarding must not replace the isolated runtime environment' }
        $value = [Environment]::GetEnvironmentVariable($name,'Process')
        if ([string]::IsNullOrWhiteSpace($value) -or $value.Length -gt 8192 -or $value.IndexOfAny([char[]]@(0,10,13)) -ge 0) { throw 'A selected credential environment value is missing or invalid' }
        $Variables.Add($name,$value)
    }
}
function Get-Digest([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $hash.Dispose() }
}
function Text-Digest([string]$Text) {
    return Bytes-Digest $utf8.GetBytes($Text)
}
function Bytes-Digest([byte[]]$Bytes) {
    $hash = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hash.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() }
    finally { $hash.Dispose() }
}
function Write-Json([string]$Path, $Value) {
    Assert-OrdinaryPath $Path
    $temporary = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 12), $utf8)
    if ([IO.File]::Exists($Path)) { [IO.File]::Replace($temporary,$Path,[NullString]::Value) }
    else { [IO.File]::Move($temporary,$Path) }
}
function Below([string]$Parent, [string]$Child) {
    return (Plain-Path $Child).StartsWith(((Plain-Path $Parent).TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)
}
function Plain-Path([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if ($full.StartsWith('\\?\UNC\')) { return '\\' + $full.Substring(8) }
    if ($full.StartsWith('\\?\')) { return $full.Substring(4) }
    return $full
}
function Native-Path([string]$Path,[switch]$ForceExtended) {
    $full = Plain-Path $Path
    if (-not $ForceExtended -and $full.Length -lt 260) { return $full }
    if ($full.StartsWith('\\')) { return '\\?\UNC\' + $full.Substring(2) }
    return '\\?\' + $full
}
function Assert-OrdinaryPath([string]$Path) {
    $current = Plain-Path $Path
    while (-not [string]::IsNullOrEmpty($current)) {
        try {
            $attributes = [IO.File]::GetAttributes((Native-Path $current))
            if (($attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Bootstrap paths must not traverse reparse points: $current" }
        } catch [IO.FileNotFoundException] { }
        catch [IO.DirectoryNotFoundException] { }
        $current = [IO.Path]::GetDirectoryName($current)
    }
}
function Python-Arguments([string]$Script,[string[]]$Arguments) {
    $startup = 'import sys;sys.path[:]=[p if p.startswith("\\\\?\\") else "\\\\?\\UNC\\"+p[2:] if p.startswith("\\\\") else "\\\\?\\"+p for p in sys.path];import runpy;sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")'
    return @('-I','-B','-X','utf8','-c',$startup,$Script) + $Arguments
}
function Download-Checked([string]$Url,[long]$ExpectedBytes,[string]$ExpectedDigest,[string]$Target,[string]$Receipt) {
    $temporary=$Target+'.download-'+[Guid]::NewGuid().ToString('N')
    $request=[Net.HttpWebRequest]::Create($Url)
    $request.Timeout=30000; $request.ReadWriteTimeout=30000; $request.UserAgent='ai-skills-bootstrap/1'
    $response=$null; $inputStream=$null; $outputStream=$null
    $clock=[Diagnostics.Stopwatch]::StartNew(); $count=0L; $buffer=New-Object byte[] 65536
    try {
        $response=$request.GetResponse()
        if([int]$response.StatusCode -ne 200) { throw 'A pinned download did not return HTTP 200' }
        $inputStream=$response.GetResponseStream()
        $outputStream=[IO.File]::Open((Native-Path $temporary),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        while(($read=$inputStream.Read($buffer,0,$buffer.Length)) -gt 0) {
            $count+=$read
            if($count -gt $ExpectedBytes -or $clock.Elapsed.TotalSeconds -gt 180) { throw 'A pinned download exceeded its declared bounds' }
            $outputStream.Write($buffer,0,$read)
        }
    } finally {
        if($null -ne $outputStream) { $outputStream.Dispose() }
        if($null -ne $inputStream) { $inputStream.Dispose() }
        if($null -ne $response) { $response.Dispose() }
    }
    $digest=Get-Digest (Native-Path $temporary)
    Write-Json $Receipt @{url=$Url;status_code=200;bytes=$count;sha256=$digest}
    if($count -ne $ExpectedBytes -or $digest -cne $ExpectedDigest) { throw 'A pinned download integrity check failed' }
    [IO.File]::Move((Native-Path $temporary),(Native-Path $Target))
}
function Tool-Resources([string]$ToolHome,$Pin) {
    if($Pin.psobject.Properties.Name -notcontains 'resources') { return $true }
    foreach($resource in $Pin.resources.psobject.Properties) {
        if($resource.Name -match '(^/|[\\:]|(^|/)\.\.?(/|$))') { throw 'Noncanonical pinned resource path' }
        $target=[IO.Path]::Combine($ToolHome,$resource.Name.Replace('/','\'))
        Assert-OrdinaryPath $target
        if([IO.File]::Exists((Native-Path $target))) {
            if((Get-Digest (Native-Path $target)) -cne $resource.Value.sha256) { return $false }
        } else {
            [void][IO.Directory]::CreateDirectory((Native-Path ([IO.Path]::GetDirectoryName($target))))
            Download-Checked $resource.Value.url $resource.Value.bytes $resource.Value.sha256 $target ($target+'.download.json')
        }
    }
    return $true
}
function Tool-Aliases([string]$ToolHome,$Pin) {
    if ($Pin.psobject.Properties.Name -notcontains 'aliases') { return $true }
    foreach ($alias in $Pin.aliases.psobject.Properties) {
        foreach($name in @($alias.Name,[string]$alias.Value)) { if($name -match '(^/|[\\:]|(^|/)\.\.?(/|$))') { throw 'Noncanonical executable alias' } }
        $source=[IO.Path]::Combine($ToolHome,([string]$alias.Value).Replace('/','\'))
        $target=[IO.Path]::Combine($ToolHome,$alias.Name.Replace('/','\'))
        Assert-OrdinaryPath $source; Assert-OrdinaryPath $target
        $expected=$Pin.files.($alias.Value).sha256
        if([IO.File]::Exists((Native-Path $target))) {
            if((Get-Digest (Native-Path $target)) -cne $expected) { return $false }
        } else {
            [void][IO.Directory]::CreateDirectory((Native-Path ([IO.Path]::GetDirectoryName($target))))
            [IO.File]::Copy((Native-Path $source),(Native-Path $target))
            if((Get-Digest (Native-Path $target)) -cne $expected) { throw 'Executable alias differs from its admitted original' }
        }
    }
    return $true
}
function Ensure-Tool([string]$Name,$Pin,[string]$ToolRoot) {
    $pointer = Join-Path $ToolRoot ($Name + '.json')
    Assert-OrdinaryPath $pointer
    if ([IO.File]::Exists($pointer)) {
        try {
            $saved = [IO.File]::ReadAllText($pointer) | ConvertFrom-Json
            if ((Below $ToolRoot $saved.home) -and [IO.Directory]::Exists($saved.home)) {
                Assert-OrdinaryPath $saved.home
                $valid = $true
                foreach ($file in $Pin.files.psobject.Properties) {
                    $target = [IO.Path]::Combine($saved.home,$file.Name.Replace('/','\'))
                    Assert-OrdinaryPath $target
                    if (-not [IO.File]::Exists((Native-Path $target)) -or (Get-Digest (Native-Path $target)) -ne $file.Value.sha256) { $valid=$false; break }
                }
                if ($valid -and (Tool-Resources $saved.home $Pin) -and (Tool-Aliases $saved.home $Pin)) { return $saved.home }
            }
        } catch { }
    }
    $toolHome = Join-Path $ToolRoot ($Name + '-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($toolHome)
    $archivePath = [IO.Path]::Combine($toolHome,'archive.zip')
    Download-Checked $Pin.url $Pin.archive_bytes $Pin.archive_sha256 $archivePath (Join-Path $toolHome 'download.json')
    if($Pin.psobject.Properties.Name -contains 'format') {
        $toolHome=Expand-QualifiedPayload $archivePath $toolHome $Pin
    } else {
    $stream = [IO.File]::OpenRead((Native-Path $archivePath))
    $archive = New-Object IO.Compression.ZipArchive($stream,[IO.Compression.ZipArchiveMode]::Read)
    try {
        $expected = @($Pin.files.psobject.Properties.Name)
        $mapped = $Pin.psobject.Properties.Name -contains 'file_map'
        $selected = if($mapped) { @($Pin.file_map.psobject.Properties.Name) } else { $expected }
        $extracted=0
        $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
        foreach ($entry in $archive.Entries) {
            $name = $entry.FullName
            if ($name -match '(^/|[\\:]|(^|/)\.\.?(/|$))' -or -not $seen.Add($name)) { throw 'Bootstrap archive contains a noncanonical or duplicate path' }
            if ($name.EndsWith('/')) {
                if (-not $mapped -and -not @($expected | Where-Object { $_.StartsWith($name,[StringComparison]::Ordinal) }).Count) { throw 'Bootstrap archive contains an undeclared directory' }
                continue
            }
            if ($selected -cnotcontains $name) {
                if($mapped) { continue }
                throw 'Bootstrap archive contains an unexpected file'
            }
            $destination = if($mapped) { [string]$Pin.file_map.$name } else { $name }
            if($destination -match '(^/|[\\:]|(^|/)\.\.?(/|$))' -or $expected -cnotcontains $destination) { throw 'Noncanonical admitted archive destination' }
            $declared = $Pin.files.$destination
            if ($entry.Length -ne $declared.bytes -or (($entry.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000) { throw 'Bootstrap archive member type or size differs' }
            $target = [IO.Path]::Combine($toolHome,$destination.Replace('/','\'))
            [void][IO.Directory]::CreateDirectory((Native-Path ([IO.Path]::GetDirectoryName($target))))
            $file = [IO.File]::Open((Native-Path $target),[IO.FileMode]::CreateNew)
            $member = $entry.Open()
            try { $member.CopyTo($file) } finally { $member.Dispose(); $file.Dispose() }
            if ((Get-Digest (Native-Path $target)) -ne $declared.sha256) { throw 'Bootstrap member integrity differs' }
            $extracted++
        }
        if ($extracted -ne $expected.Count) { throw 'Bootstrap archive is missing declared files' }
    } finally { $archive.Dispose(); $stream.Dispose() }
    }
    if(-not (Tool-Resources $toolHome $Pin) -or -not (Tool-Aliases $toolHome $Pin)) { throw 'Fresh resource or executable alias admission failed' }
    Write-Json $pointer @{home=$toolHome; archive_sha256=$Pin.archive_sha256}
    return $toolHome
}
if ([string]::IsNullOrEmpty($CacheRoot)) {
    $CacheRoot = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'ai-skills-toolchains'
}
$CacheRoot = Plain-Path $CacheRoot
$namespace = Join-Path $CacheRoot ((Text-Digest $rootPath.ToLowerInvariant()).Substring(0,16))
Assert-OrdinaryPath $namespace
if ([IO.Directory]::Exists($namespace) -and -not [IO.File]::Exists((Join-Path $namespace 'owner.json'))) {
    $existing = @([IO.Directory]::EnumerateFileSystemEntries($namespace) | Where-Object { [IO.Path]::GetFileName($_) -cne 'bootstrap.lock' })
    if ($existing.Count -ne 0) { throw 'Refusing to adopt an existing cache without an ownership record' }
}
[void][IO.Directory]::CreateDirectory($namespace)
foreach ($item in @($namespace, $CacheRoot)) {
    if (([IO.File]::GetAttributes($item) -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'A bootstrap cache must be an ordinary directory' }
}
$lockPath = Join-Path $namespace 'bootstrap.lock'
Assert-OrdinaryPath $lockPath
$wait = [Diagnostics.Stopwatch]::StartNew()
$lock = $null
while ($null -eq $lock) {
    try { $lock = [IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None) }
    catch [IO.IOException] {
        if ($wait.Elapsed.TotalSeconds -gt $LockTimeoutSeconds) { throw 'Another bootstrap operation still owns the cache lock' }
        Start-Sleep -Milliseconds 200
    }
}
try {
    $ownerPath = Join-Path $namespace 'owner.json'
    Assert-OrdinaryPath $ownerPath
    if ([IO.File]::Exists($ownerPath)) {
        $owner = [IO.File]::ReadAllText($ownerPath) | ConvertFrom-Json
        if ($owner.schema_version -ne 1 -or $owner.purpose -cne 'ai-skills-toolchains' -or -not $owner.source_root.Equals($rootPath,[StringComparison]::OrdinalIgnoreCase)) { throw 'The cache ownership record differs from the selected checkout' }
    } else {
        $existing = @([IO.Directory]::EnumerateFileSystemEntries($namespace) | Where-Object { [IO.Path]::GetFileName($_) -cne 'bootstrap.lock' })
        if ($existing.Count -ne 0) { throw 'Refusing to adopt an existing cache without an ownership record' }
        Write-Json $ownerPath @{schema_version=1; purpose='ai-skills-toolchains'; source_root=$rootPath}
    }
    $toolRoot = Join-Path $namespace 'tools'
    Assert-OrdinaryPath $toolRoot
    [void][IO.Directory]::CreateDirectory($toolRoot)
    $enginePinPath = Join-Path $bootstrapHome 'powershell.json'
    $enginePin = [IO.File]::ReadAllText($enginePinPath) | ConvertFrom-Json
    $engineHome = Plain-Path (Ensure-Tool 'powershell' $enginePin $toolRoot)
    $engine = Join-Path $engineHome 'pwsh.exe'
    $currentEngine = [Diagnostics.Process]::GetCurrentProcess()
    try { $currentEnginePath = $currentEngine.MainModule.FileName }
    finally { $currentEngine.Dispose() }
    if (-not (Plain-Path $currentEnginePath).Equals((Plain-Path $engine),[StringComparison]::OrdinalIgnoreCase)) {
        # The first stage uses only managed APIs; compilation runs in the admitted engine.
        $lock.Dispose()
        $lock = $null
        $parameters = @('-NoLogo','-NoProfile','-NonInteractive','-File',(Join-Path $bootstrapHome 'bootstrap.ps1'),'-Root',$rootPath,'-CacheRoot',$CacheRoot,'-Profile',$Profile,'-LockTimeoutSeconds',[string]$LockTimeoutSeconds)
        if (-not [string]::IsNullOrEmpty($CommandBase64)) { $parameters += @('-CommandBase64',$CommandBase64) }
        if (-not [string]::IsNullOrEmpty($CredentialEnvironmentBase64)) { $parameters += @('-CredentialEnvironmentBase64',$CredentialEnvironmentBase64) }
        $engineEnvironment = @{
            PSModulePath = (Join-Path $engineHome 'Modules')
            PSModuleAnalysisCachePath = (Join-Path $namespace 'powershell-module-analysis.cache')
            POWERSHELL_TELEMETRY_OPTOUT = '1'
            POWERSHELL_UPDATECHECK = 'Off'
        }
        $previousEnvironment = @{}
        try {
            foreach ($name in $engineEnvironment.Keys) {
                $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name,'Process')
                [Environment]::SetEnvironmentVariable($name,$engineEnvironment[$name],'Process')
            }
            & $engine @parameters
            $engineExit = $LASTEXITCODE
        } finally {
            foreach ($name in $previousEnvironment.Keys) { [Environment]::SetEnvironmentVariable($name,$previousEnvironment[$name],'Process') }
        }
        exit $engineExit
    }
    if ($PSVersionTable.PSVersion.ToString() -cne $enginePin.version) { throw 'The admitted PowerShell runtime version differs from its pin' }
    Add-Type -Path (Join-Path $bootstrapHome 'OwnedProcess.cs')
    Add-Type -Path (Join-Path $bootstrapHome 'NativeCabinet.cs')
    $inputs = [ordered]@{}
    $lockedInputs = [ordered]@{}
    $requirements = New-Object 'System.Collections.Generic.List[string]'
    foreach ($relative in ($spec.requirements | Sort-Object)) {
        if ($relative -match '(^/|\\|:|(^|/)\.\.?(/|$))') { throw 'Noncanonical requirement path' }
        $path = Join-Path $rootPath $relative
        if (-not (Below $rootPath $path)) { throw 'Requirements must remain inside the selected checkout' }
        Assert-OrdinaryPath $path
        $lockedInputs[$relative] = [IO.File]::ReadAllBytes($path)
        $inputs[$relative] = Bytes-Digest $lockedInputs[$relative]
    }
    $runtimeIdentity = if ($Profile -in @('git','codex')) { 'none' } else { $manifest.pythons.($spec.python).archive_sha256 }
    $nativeIdentity=if($spec.python -eq '3.13.18'){$manifest.microsoft_runtime.archive_sha256}else{''}
    $sourceIdentity = Text-Digest (($inputs | ConvertTo-Json -Compress) + $runtimeIdentity + $nativeIdentity + $Profile + '|venv-graph-v3')
    $logs = Join-Path $namespace ('logs-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($logs)
    $inputDirectory=Join-Path $logs 'requirements'
    [void][IO.Directory]::CreateDirectory($inputDirectory)
    foreach($relative in $lockedInputs.Keys) {
        $copy=Join-Path $inputDirectory ($requirements.Count.ToString() + '.txt')
        [IO.File]::WriteAllBytes($copy,$lockedInputs[$relative])
        $requirements.Add($copy)
    }
    $sources = [ordered]@{}
    foreach ($name in @('dev.ps1','toolchains/bootstrap/bootstrap.ps1','toolchains/bootstrap/powershell.json','toolchains/bootstrap/codex.json','toolchains/bootstrap/OwnedProcess.cs','tools/_bootstrap_doctor.py','tools/_bootstrap_launch.py','tools/_bootstrap_archive.py','toolchains/bootstrap/manifest.json','toolchains/bootstrap/ArchiveLayers.ps1','toolchains/bootstrap/NativeCabinet.cs')) { $sources[$name] = Get-Digest (Join-Path $rootPath $name) }
    Write-Json (Join-Path $logs 'source.json') @{sources=$sources; requirements=$inputs; graph_identity=$sourceIdentity; bootstrap_engine=@{path=$engine; version=$enginePin.version; sha256=$enginePin.files.'pwsh.exe'.sha256}}
    $environment = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($name in @('SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','SYSTEMDRIVE')) {
        $value = [Environment]::GetEnvironmentVariable($name)
        if ([string]::IsNullOrEmpty($value)) { throw "Missing native system variable: $name" }
        $environment.Add($name,$value)
    }
    $environment.Add('PATH',[Environment]::GetFolderPath('System'))
    $temporary = Join-Path ([IO.Path]::GetTempPath()) ('as-' + [Guid]::NewGuid().ToString('N').Substring(0,12))
    Assert-OrdinaryPath $temporary
    if ([IO.Directory]::Exists($temporary) -or [IO.File]::Exists($temporary)) { throw 'The operation temporary directory must be new' }
    [void][IO.Directory]::CreateDirectory($temporary)
    $temporaryOwner = @{purpose='ai-skills-operation-temporary'; source_root=$rootPath; diagnostics=$logs}
    Write-Json (Join-Path $temporary 'owner.json') $temporaryOwner
    Write-Json (Join-Path $logs 'temporary.json') @{path=$temporary; owner=$temporaryOwner}
    $environment.Add('TEMP',$temporary)
    $environment.Add('TMP',$temporary)
    foreach ($entry in @{'HOME'='home'; 'USERPROFILE'='home'; 'APPDATA'='home\roaming'; 'LOCALAPPDATA'='home\local'; 'UV_CACHE_DIR'='uv-cache'; 'UV_PYTHON_INSTALL_DIR'='managed-python'; 'UV_TOOL_DIR'='uv-tools'; 'UV_TOOL_BIN_DIR'='unused-bin'; 'UV_PYTHON_BIN_DIR'='unused-bin'}.GetEnumerator()) {
        $path = Join-Path $namespace $entry.Value
        [void][IO.Directory]::CreateDirectory($path)
        $environment.Add($entry.Key,$path)
    }
    $environment.Add('UV_PYTHON_NO_REGISTRY','1')
    $environment['UV_PYTHON_INSTALL_DIR'] = Native-Path $environment['UV_PYTHON_INSTALL_DIR']
    $environment.Add('UV_PYTHON_INSTALL_BIN','0')
    $environment.Add('UV_NO_PROGRESS','1')
    $environment.Add('UV_LINK_MODE','copy')
    $environment.Add('UV_PYTHON_DOWNLOADS','never')
    $environment.Add('PYTHONUTF8','1')
    function Invoke-Owned([string]$Name,[string]$Executable,[string[]]$Arguments) {
        $stdout = Join-Path $logs ($Name + '.stdout.native')
        $stderr = Join-Path $logs ($Name + '.stderr.native')
        $process = [SkillsBootstrap.OwnedProcess]::Run($Executable,$Arguments,$namespace,$environment,$stdout,$stderr,600,16777216,2147483648,16)
        Write-Json (Join-Path $logs ($Name + '.process.json')) $process
        if ($process.exit_code -ne 0 -or $null -ne $process.termination_reason) { throw "Bootstrap phase failed: $Name; retained diagnostics: $logs" }
        return [IO.File]::ReadAllText($stdout,$utf8).Trim()
    }
    if ($Profile -eq 'codex') {
        $codexPin=[IO.File]::ReadAllText((Join-Path $bootstrapHome 'codex.json')) | ConvertFrom-Json
        $codexHome=Ensure-Tool 'codex' $codexPin $toolRoot
        $codex=[IO.Path]::GetFullPath([IO.Path]::Combine($codexHome,$codexPin.executable))
        if ((Invoke-Owned 'codex-version' $codex @('--version')) -cne ('codex-cli ' + $codexPin.version)) { throw 'Codex CLI version differs from its qualified release' }
        $runtimeRoot=[IO.Path]::GetFullPath([IO.Path]::Combine($codexHome,$codexPin.runtime_root))
        @{ready=$true;profile='codex';cli=$codex;package_root=$codexHome;readable_root=$runtimeRoot;version=$codexPin.version;diagnostics=$logs} | ConvertTo-Json -Compress
        return
    }
    if ($Profile -ne 'git') {
        $uvHome = Ensure-Tool 'uv' $manifest.uv $toolRoot
        $uv = Join-Path $uvHome 'uv.exe'
        $version = Invoke-Owned 'uv-version' $uv @('--version')
        if (-not $version.StartsWith(('uv ' + $manifest.uv.version + ' '))) { throw 'Bootstrap executable version differs from the manifest' }
    }
    $gitHome = Ensure-Tool 'git' $manifest.git $toolRoot
    $git = [IO.Path]::Combine($gitHome,'ucrt64\bin\git.exe')
    $gitVersion = Invoke-Owned 'git-version' $git @('--version')
    if ($gitVersion -cne ('git version ' + $manifest.git.version)) { throw 'Portable Git version differs from its manifest' }
    $gitExecPath = Invoke-Owned 'git-exec-path' $git @('--exec-path')
    if (-not (Below $gitHome $gitExecPath) -or -not [IO.Directory]::Exists($gitExecPath)) { throw 'Portable Git could not resolve its owned helpers at this cache path; select a shorter writable CacheRoot' }
    if ($Profile -eq 'git') {
        @{ready=$true;profile='git';git=$git;diagnostics=$logs} | ConvertTo-Json -Compress
        return
    }
    $additionalPaths=@()
    $bash=[IO.Path]::Combine($gitHome,'usr\bin\bash.exe')
    $additionalPaths+=[IO.Path]::GetDirectoryName($bash)
    $bashVersion=Invoke-Owned 'bash-version' $bash @('--version')
    if(-not $bashVersion.StartsWith($manifest.git.bash_version)) { throw 'Bundled GNU Bash version differs from its qualified package' }
    if(-not (Invoke-Owned 'sleep-version' ([IO.Path]::Combine($gitHome,'usr\bin\sleep.exe')) @('--version')).StartsWith($manifest.git.sleep_version)) { throw 'GNU sleep differs from its pinned SDK resource' }
    if(-not (Invoke-Owned 'cygpath-version' ([IO.Path]::Combine($gitHome,'usr\bin\cygpath.exe')) @('--version')).StartsWith($manifest.git.cygpath_version)) { throw 'Native path conversion differs from its pinned SDK resource' }
    if($Profile -eq 'validation') {
        $nodeHome=Ensure-Tool 'node' $manifest.node $toolRoot
        $node=[IO.Path]::Combine($nodeHome,'node.exe')
        if((Invoke-Owned 'node-version' $node @('--version')) -cne $manifest.node.version) { throw 'Node version differs from its primary release' }
        $jdkHome=Ensure-Tool 'jdk' $manifest.jdk $toolRoot
        $javaHome=[IO.Path]::Combine($jdkHome,$manifest.jdk.home)
        $java=[IO.Path]::Combine($javaHome,'bin\java.exe')
        $javac=[IO.Path]::Combine($javaHome,'bin\javac.exe')
        if(-not (Invoke-Owned 'java-version' $java @('--version')).StartsWith(('openjdk ' + $manifest.jdk.java_version + ' '))) { throw 'Java runtime differs from its qualified archive' }
        if((Invoke-Owned 'javac-version' $javac @('--version')) -cne ('javac ' + $manifest.jdk.java_version)) { throw 'Java compiler differs from its qualified archive' }
        $additionalPaths+=$nodeHome
        $additionalPaths+=[IO.Path]::GetDirectoryName($java)
        $environment['JAVA_HOME']=$javaHome
    }
    if($spec.python -eq '3.13.18') {
        $archiveHome=Ensure-Tool 'python-archive-helper' $manifest.pythons.'3.14.10' $toolRoot
        $archivePython=Join-Path $archiveHome 'tools/python.exe'
    }
    $pythonHome = Ensure-Tool ('python-' + $spec.python) $manifest.pythons.($spec.python) $toolRoot
    $executable=if($spec.python -eq '3.13.18'){'python.exe'}else{'tools\python.exe'}
    $basePython = [IO.Path]::Combine($pythonHome,$executable)
    $activePath = Join-Path $namespace ($Profile + '-' + $sourceIdentity.Substring(0,16) + '.json')
    Assert-OrdinaryPath $activePath
    $imports = @('json','ssl','venv','hashlib','pip')
    if ($Profile -eq 'validation') { $imports += @('yaml','jsonschema','referencing','pytest','hypothesis','pytest_cov','xdist','matplotlib') }
    function Probe([string]$Name,[string]$Interpreter,[string]$PackageDirectory) {
        $profileRoot=[IO.Path]::GetDirectoryName([IO.Path]::GetDirectoryName((Plain-Path $Interpreter)))
        $configuration=Join-Path $profileRoot 'pyvenv.cfg'
        Assert-OrdinaryPath $configuration
        $settings=@{}
        foreach($line in [IO.File]::ReadAllLines($configuration)) {
            if($line -match '^([^=]+) = (.*)$') {
                $key=$matches[1].Trim()
                if($settings.ContainsKey($key)) { throw 'A virtual environment configuration contains duplicate fields' }
                $settings[$key]=$matches[2].Trim()
            }
        }
        $baseHome=[IO.Path]::GetDirectoryName($basePython)
        if($settings['include-system-site-packages'] -cne 'false' -or -not (Plain-Path $settings['home']).Equals((Plain-Path $baseHome),[StringComparison]::OrdinalIgnoreCase)) { throw 'The virtual environment is not bound to its isolated qualified base' }
        $arguments = Python-Arguments (Join-Path $rootPath 'tools/_bootstrap_doctor.py') @('--packages',(Native-Path $PackageDirectory))
        foreach ($requirement in $requirements) { $arguments += @('--requirements',$requirement) }
        foreach ($module in $imports) { $arguments += @('--import',$module) }
        $observed=Invoke-Owned $Name $Interpreter $arguments
        $details=$observed | ConvertFrom-Json
        if($details.python -ne $spec.python -or $details.implementation -cne 'cpython' -or $details.bits -ne 64 -or $details.isolated -ne 1 -or $details.no_user_site -ne 1 -or -not (Plain-Path $details.prefix).Equals((Plain-Path $profileRoot),[StringComparison]::OrdinalIgnoreCase) -or -not (Plain-Path $details.base_prefix).Equals((Plain-Path $baseHome),[StringComparison]::OrdinalIgnoreCase)) { throw 'Runtime readiness differs from its isolated qualified environment' }
        return $observed
    }
    $ready = $false
    $python = $null
    if ([IO.File]::Exists($activePath)) {
        try {
            $active = [IO.File]::ReadAllText($activePath) | ConvertFrom-Json
            if ($active.source_identity -eq $sourceIdentity -and (Below $namespace $active.home)) {
                Assert-OrdinaryPath $active.home
                $python = [IO.Path]::Combine($active.home,'Scripts\python.exe')
                if (-not (Plain-Path $active.python).Equals((Plain-Path $python),[StringComparison]::OrdinalIgnoreCase)) { throw 'Profile interpreter escaped its owned environment' }
                Assert-OrdinaryPath $python
                $packages = [IO.Path]::Combine($active.home,'Lib\site-packages')
                if ([IO.File]::Exists($python)) {
                    $observed = Probe 'existing-readiness' $python $packages
                    $ready = $true
                }
            }
        } catch { $ready=$false }
    }
    if (-not $ready) {
        $profileHome = Join-Path $namespace ('profile-' + [Guid]::NewGuid().ToString('N'))
        [void](Invoke-Owned 'venv' $basePython @('-I','-B','-m','venv','--without-pip',$profileHome))
        $python = [IO.Path]::Combine($profileHome,'Scripts\python.exe')
        $packages = [IO.Path]::Combine($profileHome,'Lib\site-packages')
        if ($requirements.Count -gt 0) {
            [void](Invoke-Owned 'packages' $uv (@('--no-config','pip','sync','--python',(Native-Path $python),'--require-hashes','--only-binary=:all:','--default-index','https://pypi.org/simple') + $requirements.ToArray()))
        }
        $observed = Probe 'readiness' $python $packages
        $details = $observed | ConvertFrom-Json
        if ($details.python -ne $spec.python -or -not (Plain-Path $details.prefix).Equals((Plain-Path $profileHome),[StringComparison]::OrdinalIgnoreCase)) { throw 'Runtime readiness differs from its selected profile' }
        Write-Json $activePath @{home=$profileHome; python=$python; source_identity=$sourceIdentity; observation=$observed}
    }
    $readyResult = @{ready=$true; profile=$Profile; python=$python; packages=(Native-Path $packages); git=$git; newly_installed=(-not $ready); diagnostics=$logs}
} finally { if ($null -ne $lock) { $lock.Dispose() } }
if ([string]::IsNullOrEmpty($CommandBase64)) {
    $readyResult | ConvertTo-Json -Compress
} else {
    $commandJson = $utf8.GetString([Convert]::FromBase64String($CommandBase64))
    $command = ConvertFrom-Json -InputObject $commandJson -NoEnumerate
    if ($command -isnot [Array] -or -not $commandJson.TrimStart().StartsWith('[') -or $command.Count -eq 0 -or @($command | Where-Object { $_ -isnot [string] }).Count) { throw 'The development command must be a nonempty array of strings' }
    $environment['PATH'] = (@([IO.Path]::GetDirectoryName($python),[IO.Path]::GetDirectoryName($uv),[IO.Path]::GetDirectoryName($git)) + $additionalPaths + @((Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell\v1.0'),[Environment]::GetFolderPath('System'))) -join ';'
    $environment['VIRTUAL_ENV'] = [IO.Path]::GetDirectoryName([IO.Path]::GetDirectoryName($python))
    $environment['AI_SKILLS_BOOTSTRAP_DIAGNOSTICS'] = $logs
    $environment['GIT_CONFIG_NOSYSTEM']='1'; $environment['GIT_CONFIG_GLOBAL']='NUL'; $environment['GIT_OPTIONAL_LOCKS']='0'
    $environment['AI_SKILLS_GIT']=$git
    $environment['AI_SKILLS_BASH']=$bash
    $environment['AI_SKILLS_UNIX_BIN']=[IO.Path]::GetDirectoryName($bash)
    $environment['AI_SKILLS_DASH']=[IO.Path]::Combine($gitHome,'usr\bin\dash.exe')
    Forward-CredentialEnvironment $CredentialEnvironmentBase64 $environment
    $arguments = Python-Arguments (Join-Path $rootPath 'tools/_bootstrap_launch.py') (@('--packages',(Native-Path $packages),'--root',$rootPath,'--') + $command)
    $stdout = Join-Path $logs 'command.stdout.native'; $stderr = Join-Path $logs 'command.stderr.native'
    $process = [SkillsBootstrap.OwnedProcess]::Run($python,$arguments,$rootPath,$environment,$stdout,$stderr,1800,16777216,4294967296,64)
    Write-Json (Join-Path $logs 'command.process.json') $process
    [Console]::Out.Write([IO.File]::ReadAllText($stdout,$utf8)); [Console]::Error.Write([IO.File]::ReadAllText($stderr,$utf8))
    if ($null -ne $process.termination_reason -or $process.active_processes_after_cleanup -ne 0) { throw "Development command did not complete normally; retained diagnostics: $logs" }
    exit $process.exit_code
}
