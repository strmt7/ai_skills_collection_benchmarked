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
& $shell @parameters
exit $LASTEXITCODE
