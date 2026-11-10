param([string]$OutputDirectory)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Directory]::GetParent($PSScriptRoot).FullName
$utf8 = New-Object Text.UTF8Encoding($false)
if ([string]::IsNullOrEmpty($OutputDirectory)) {
    $OutputDirectory = Join-Path $root ('.venv/bootstrap-qualification/' + [Guid]::NewGuid().ToString('N'))
}
$output = [IO.Path]::GetFullPath($OutputDirectory)
if (-not $output.StartsWith((Join-Path $root '.venv/'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Qualification output must be a fresh directory in this checkout cache'
}
if ([IO.Directory]::Exists($output)) { throw 'Qualification output already exists' }
[void][IO.Directory]::CreateDirectory($output)
Add-Type -Path (Join-Path $root 'toolchains/bootstrap/OwnedProcess.cs')
Add-Type -TypeDefinition @'
using System;
using System.Threading.Tasks;
public static class BootstrapConcurrentQualification {
    static object[] Arguments(object[] values) {
        var result = new object[values.Length];
        for (int index = 0; index < values.Length; index++) {
            object value = values[index];
            while (value != null && value.GetType().FullName == "System.Management.Automation.PSObject")
                value = value.GetType().GetProperty("BaseObject").GetValue(value, null);
            result[index] = value;
        }
        return result;
    }
    public static object[] Run(Type owner, object[] left, object[] right) {
        var method = owner.GetMethod("Run");
        var first = Task.Factory.StartNew(() => method.Invoke(null, Arguments(left)));
        var second = Task.Factory.StartNew(() => method.Invoke(null, Arguments(right)));
        Task.WaitAll(first, second);
        return new object[] { first.Result, second.Result };
    }
}
'@

function Write-Record([string]$Path, $Value) {
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 16), $utf8)
}
function Host-State {
    $registry = [ordered]@{}
    foreach ($path in @('Registry::HKEY_CURRENT_USER\Software\Python', 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Python', 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Python', 'Registry::HKEY_CURRENT_USER\Software\Microsoft\PowerShell', 'Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PowerShell')) {
        $values = @()
        if (Test-Path -LiteralPath $path) {
            foreach ($key in (@(Get-Item -LiteralPath $path) + @(Get-ChildItem -LiteralPath $path -Recurse))) {
                foreach ($name in ($key.GetValueNames() | Sort-Object)) {
                    $values += [ordered]@{key=$key.Name; name=$name; kind=[string]$key.GetValueKind($name); value=$key.GetValue($name)}
                }
            }
        }
        $registry[$path] = $values
    }
    return [ordered]@{user_path=[Environment]::GetEnvironmentVariable('PATH','User'); machine_path=[Environment]::GetEnvironmentVariable('PATH','Machine'); python_registry=$registry}
}

$sourceNames = @('dev.ps1', 'toolchains/bootstrap/bootstrap.ps1', 'toolchains/bootstrap/powershell.json', 'toolchains/bootstrap/codex.json', 'toolchains/bootstrap/OwnedProcess.cs', 'toolchains/bootstrap/NativeCabinet.cs', 'toolchains/bootstrap/ArchiveLayers.ps1', 'tools/_bootstrap_archive.py', 'toolchains/bootstrap/manifest.json', 'toolchains/bootstrap/requirements.txt', 'tools/_bootstrap_doctor.py', 'tools/_bootstrap_launch.py', 'requirements-dev-lock.txt', 'requirements-reports-lock.txt', 'tests/qualify_windows_bootstrap.ps1')
$sources = [ordered]@{}
foreach ($name in $sourceNames) { $sources[$name] = (Get-FileHash -LiteralPath (Join-Path $root $name) -Algorithm SHA256).Hash.ToLowerInvariant() }
$before = Host-State
Write-Record (Join-Path $output 'host-before.json') $before
$cache = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) ('ai-skills-qualification/' + [Guid]::NewGuid().ToString('N').Substring(0,12))
$environment = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($name in @('SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','SYSTEMDRIVE','PROCESSOR_ARCHITECTURE','TEMP','TMP','LOCALAPPDATA','APPDATA','USERPROFILE')) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if (-not [string]::IsNullOrEmpty($value)) { $environment.Add($name,$value) }
}
$environment.Add('PATH',[Environment]::GetFolderPath('System'))
$privateTemporary = Join-Path ([IO.Path]::GetTempPath()) ("skills-bootstrap ' " + [char]0x03a9 + '-' + [Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($privateTemporary)
Write-Record (Join-Path $privateTemporary 'owner.json') @{purpose='ai-skills-bootstrap-qualification'; source_root=$root; diagnostics=$output}
$environment['TEMP'] = $privateTemporary
$environment['TMP'] = $privateTemporary
$environment['GIT_CONFIG_COUNT'] = '2'
$environment['GIT_CONFIG_KEY_0'] = 'core.longpaths'
$environment['GIT_CONFIG_VALUE_0'] = 'false'
$environment['GIT_CONFIG_KEY_1'] = 'alias.parent-scope-probe'
$environment['GIT_CONFIG_VALUE_1'] = 'must-not-cross'
$shell = Join-Path ([Environment]::GetFolderPath('System')) 'WindowsPowerShell/v1.0/powershell.exe'
$entry = Join-Path $root 'dev.ps1'
$controls = New-Object 'System.Collections.Generic.List[object]'
function Process-Arguments([string]$Name, [string[]]$Arguments) {
    return [object[]]@($shell, $Arguments, $root, $environment, (Join-Path $output ($Name+'.stdout.native')), (Join-Path $output ($Name+'.stderr.native')), [int]900, [long]16777216, [long]4294967296, [int]64)
}
function Invoke-Control([string]$Name, [string[]]$Command, [int]$Expected=0, [string]$SelectedCache=$cache) {
    $arguments = @('-NoLogo','-NoProfile','-NonInteractive','-File',$entry,'--cache-root',$SelectedCache) + $Command
    $process = [SkillsBootstrap.OwnedProcess]::Run($shell,$arguments,$root,$environment,(Join-Path $output ($Name+'.stdout.native')),(Join-Path $output ($Name+'.stderr.native')),900,16777216,4294967296,64)
    $controls.Add(@{name=$Name; process=$process})
    if ($process.exit_code -ne $Expected -or $null -ne $process.termination_reason -or $process.active_processes_after_cleanup -ne 0) { throw "Control failed: $Name; diagnostics: $output" }
    return [IO.File]::ReadAllText((Join-Path $output ($Name+'.stdout.native')),$utf8)
}
function Invoke-NativeControl([string]$Name, [string[]]$Arguments, [int]$Seconds, [long]$Budget, $Reason) {
    $process = [SkillsBootstrap.OwnedProcess]::Run($fresh.python,$Arguments,$root,$environment,(Join-Path $output ($Name+'.stdout.native')),(Join-Path $output ($Name+'.stderr.native')),$Seconds,$Budget,1073741824,16)
    $controls.Add(@{name=$Name; process=$process})
    if ($process.termination_reason -cne $Reason -or $process.active_processes_after_cleanup -ne 0) { throw "Native process control failed: $Name" }
    return $process
}

$failure = $null
try {
    $cliFresh = (Invoke-Control 'codex-fresh' @('codex')) | ConvertFrom-Json
    $cliReuse = (Invoke-Control 'codex-reuse' @('codex')) | ConvertFrom-Json
    $cliPin = [IO.File]::ReadAllText((Join-Path $root 'toolchains/bootstrap/codex.json')) | ConvertFrom-Json
    if (-not $cliFresh.ready -or $cliFresh.profile -cne 'codex' -or $cliFresh.version -cne $cliPin.version -or $cliFresh.cli -cne $cliReuse.cli) { throw 'Pinned Codex setup or reuse differs from the contract' }
    $cliNamespace=[IO.Path]::GetDirectoryName($cliFresh.diagnostics)
    $cliTools=Join-Path $cliNamespace 'tools'
    if (@([IO.Directory]::EnumerateDirectories($cliTools) | Where-Object { [IO.Path]::GetFileName($_) -match '^(git|uv|python|node|jdk)' }).Count -ne 0) { throw 'The CLI-only profile installed unrelated tools' }
    $helper=Join-Path $cliFresh.readable_root 'codex-resources/codex-command-runner.exe'
    if (-not $helper.StartsWith(($cliTools+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'The CLI recovery fixture escaped its owned cache' }
    [IO.File]::Move($helper,($helper+'.qualification-original'))
    $cliRecovered=(Invoke-Control 'codex-missing-helper' @('codex')) | ConvertFrom-Json
    if ($cliRecovered.cli -ceq $cliFresh.cli -or -not [IO.File]::Exists(($helper+'.qualification-original'))) { throw 'CLI helper recovery did not preserve the previous installation' }
    foreach ($file in $cliPin.files.psobject.Properties) {
        $path=Join-Path $cliRecovered.package_root $file.Name
        if (-not [IO.File]::Exists($path) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -cne $file.Value.sha256) { throw 'Recovered CLI payload differs from the complete release' }
    }
    $license=Join-Path $cliRecovered.package_root 'LICENSE'
    if (-not $license.StartsWith(($cliTools+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'The CLI license fixture escaped its owned cache' }
    [IO.File]::Move($license,($license+'.qualification-original'))
    $cliLicensed=(Invoke-Control 'codex-missing-license' @('codex')) | ConvertFrom-Json
    if ($cliLicensed.cli -cne $cliRecovered.cli -or (Get-FileHash -LiteralPath $license -Algorithm SHA256).Hash.ToLowerInvariant() -cne $cliPin.resources.LICENSE.sha256) { throw 'Missing CLI license was not restored in its admitted profile' }
    [void](Invoke-Control 'codex-execution-arguments' @('codex','exec','must-not-run') 1)
    [void](Invoke-Control 'codex-credential-forwarding' @('--credential-env','AI_SKILLS_QUALIFICATION_TOKEN','codex') 1)
    $cliCommand=[string[]]@('-NoLogo','-NoProfile','-NonInteractive','-File',$entry,'--cache-root',$cache,'codex')
    $cliPair=[BootstrapConcurrentQualification]::Run([SkillsBootstrap.OwnedProcess],(Process-Arguments 'codex-concurrent-first' $cliCommand),(Process-Arguments 'codex-concurrent-second' $cliCommand))
    foreach ($process in $cliPair) { if ($process.exit_code -ne 0 -or $null -ne $process.termination_reason -or $process.active_processes_after_cleanup -ne 0) { throw 'Concurrent CLI setup failed ownership or readiness' } }
    foreach ($name in @('codex-concurrent-first','codex-concurrent-second')) {
        $cliConcurrent=[IO.File]::ReadAllText((Join-Path $output ($name+'.stdout.native'))) | ConvertFrom-Json
        if ($cliConcurrent.cli -cne $cliRecovered.cli) { throw 'Concurrent CLI setup did not reuse the admitted installation' }
    }
    $controls.Add(@{name='codex-concurrent-reuse'; processes=$cliPair; shared_installation=$true})
    $defaultArguments=@('-NoLogo','-NoProfile','-NonInteractive','-File',$entry,'codex')
    $defaultProcess=[SkillsBootstrap.OwnedProcess]::Run($shell,$defaultArguments,$root,$environment,(Join-Path $output 'codex-default.stdout.native'),(Join-Path $output 'codex-default.stderr.native'),900,16777216,4294967296,64)
    $controls.Add(@{name='codex-default';process=$defaultProcess})
    if ($defaultProcess.exit_code -ne 0 -or $null -ne $defaultProcess.termination_reason -or $defaultProcess.active_processes_after_cleanup -ne 0) { throw 'Default CLI setup failed ownership or readiness' }
    $defaultCli=[IO.File]::ReadAllText((Join-Path $output 'codex-default.stdout.native')) | ConvertFrom-Json
    if (-not $defaultCli.ready -or -not $defaultCli.cli.StartsWith(((Join-Path $root '.venv/cli')+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'The default CLI cache is not bound to this checkout' }
    $fresh = (Invoke-Control 'fresh' @('doctor')) | ConvertFrom-Json
    $reuse = (Invoke-Control 'reuse' @('doctor')) | ConvertFrom-Json
    if (-not $fresh.ready -or -not $fresh.newly_installed -or $reuse.newly_installed -or $fresh.packages -cne $reuse.packages) { throw 'Fresh setup or reuse differs from the independent contract' }
    $version = (Invoke-Control 'single-option' @('python','--version')).Trim()
    $manifest = [IO.File]::ReadAllText((Join-Path $root 'toolchains/bootstrap/manifest.json')) | ConvertFrom-Json
    if (($version -split '\s+',2)[0] -cne $manifest.profiles.validation.python) { throw 'The single-option command was not preserved' }
    $singleScript = Join-Path $output 'single-script.py'
    [IO.File]::WriteAllText($singleScript,"print('single script command')`n",$utf8)
    if ((Invoke-Control 'single-script' @('python',$singleScript)).Trim() -cne 'single script command') { throw 'The single-script command was not preserved' }
    $values = @('', 'a"b', 'trailing\', ('Unicode '+[char]0x03bb))
    $arguments = (Invoke-Control 'arguments' (@('python','-c','import json,sys;print(json.dumps(sys.argv[1:]))') + $values)) | ConvertFrom-Json
    if ($arguments.Count -ne $values.Count) { throw 'Command argument count changed' }
    for ($index=0; $index -lt $values.Count; $index++) { if ($arguments[$index] -cne $values[$index]) { throw 'Command argument bytes changed' } }
    $context = @{entry=$entry; cache=$cache} | ConvertTo-Json -Compress
    $context = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($context))
    $program = @'
$data = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__CONTEXT__')) | ConvertFrom-Json
& $data.entry --cache-root $data.cache python -c 'import json,sys;print(json.dumps(sys.argv[1:]))' 2 '02' -3 1.25 $false
exit $LASTEXITCODE
'@
    $program = $program.Replace('__CONTEXT__',$context)
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($program))
    $process = [SkillsBootstrap.OwnedProcess]::Run($shell,@('-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',$encoded),$root,$environment,(Join-Path $output 'powershell-values.stdout.native'),(Join-Path $output 'powershell-values.stderr.native'),120,1048576,2147483648,32)
    $controls.Add(@{name='powershell-values'; process=$process})
    if ($process.exit_code -ne 0 -or $null -ne $process.termination_reason -or $process.active_processes_after_cleanup -ne 0) { throw 'Direct PowerShell invocation failed' }
    $observed = [IO.File]::ReadAllText((Join-Path $output 'powershell-values.stdout.native')) | ConvertFrom-Json
    $expected = @('2','02','-3','1.25','False')
    if ($observed.Count -ne $expected.Count) { throw 'Direct PowerShell argument count changed' }
    for ($index=0; $index -lt $expected.Count; $index++) { if ($observed[$index] -cne $expected[$index]) { throw 'Direct PowerShell argument value changed' } }
    $credentialName = 'AI_SKILLS_QUALIFICATION_TOKEN'
    $credentialValue = 'owned qualification fixture value'
    $environment.Add($credentialName,$credentialValue)
    $hash = [Security.Cryptography.SHA256]::Create()
    try { $credentialDigest = ([BitConverter]::ToString($hash.ComputeHash($utf8.GetBytes($credentialValue)))).Replace('-','').ToLowerInvariant() }
    finally { $hash.Dispose() }
    $absentCode = 'import os;print("AI_SKILLS_QUALIFICATION_TOKEN" not in os.environ)'
    if ((Invoke-Control 'credential-not-inherited' @('python','-c',$absentCode)).Trim() -cne 'True') { throw 'The development command inherited an undeclared credential' }
    $selectedCode = 'import hashlib,os;print(hashlib.sha256(os.environ["AI_SKILLS_QUALIFICATION_TOKEN"].encode()).hexdigest())'
    if ((Invoke-Control 'selected-credential' @('--credential-env',$credentialName,'python','-c',$selectedCode)).Trim() -cne $credentialDigest) { throw 'The explicitly selected credential was not forwarded intact' }
    [void](Invoke-Control 'duplicate-credential' @('--credential-env',$credentialName,'--credential-env',$credentialName.ToLowerInvariant(),'python','-c','raise AssertionError("must not execute")') 1)
    if (-not ([IO.File]::ReadAllText((Join-Path $output 'duplicate-credential.stderr.native'))).Contains('valid and distinct')) { throw 'The duplicate-name control failed for an unexpected reason' }
    [void]$environment.Remove($credentialName)
    [void](Invoke-Control 'missing-credential' @('--credential-env',$credentialName,'python','-c','raise AssertionError("must not execute")') 1)
    if (-not ([IO.File]::ReadAllText((Join-Path $output 'missing-credential.stderr.native'))).Contains('missing or invalid')) { throw 'The missing-credential control failed for an unexpected reason' }
    [void](Invoke-Control 'reserved-credential' @('--credential-env','PATH','python','-c','raise AssertionError("must not execute")') 1)
    if (-not ([IO.File]::ReadAllText((Join-Path $output 'reserved-credential.stderr.native'))).Contains('isolated runtime environment')) { throw 'The reserved-name control failed for an unexpected reason' }
    [void](Invoke-Control 'child-packages' @('python','-c','import subprocess,sys;subprocess.run([sys.executable,"-I","-c","import yaml,pip;print(yaml.__version__);print(pip.__version__)"],check=True)'))
    $toolProbe = @'
import os,shutil,subprocess
for name in ("git","uv","node","java","javac","bash","sleep","cygpath"):
    executable=shutil.which(name)
    if executable is None:
        raise RuntimeError("Managed tool was not discoverable: "+name)
    expected=os.environ.get("AI_SKILLS_"+name.upper())
    if name in ("sleep","cygpath"):
        expected=os.path.join(os.environ["AI_SKILLS_UNIX_BIN"],name+".exe")
    if expected is not None and not os.path.samefile(executable,expected):
        raise RuntimeError("Managed tool resolved outside its admitted installation: "+name)
    subprocess.run([executable,"--version"],check=True)
'@
    [void](Invoke-Control 'tools' @('python','-c',$toolProbe))
    $gitPathProbe = @'
import os,subprocess,tempfile
from pathlib import Path
expected={"GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"NUL","GIT_CONFIG_COUNT":"1","GIT_CONFIG_KEY_0":"core.longpaths","GIT_CONFIG_VALUE_0":"true"}
if any(os.environ.get(name)!=value for name,value in expected.items()):
    raise RuntimeError("Managed Git configuration differs from the isolated long-path contract")
git=os.environ["AI_SKILLS_GIT"]
parent=Path(os.environ["TEMP"]).resolve(strict=True)
with tempfile.TemporaryDirectory(prefix="git-path-",dir=parent) as directory:
    repository=Path(directory).resolve(strict=True)
    if not repository.is_relative_to(parent):
        raise RuntimeError("Git path fixture escaped its owned temporary directory")
    subprocess.run([git,"-C",str(repository),"init","-q"],check=True,timeout=10)
    resource=repository
    while len(str(resource).encode("utf-16-le"))//2<=300:
        resource=resource/"long-path-component-0123456789"
    resource.mkdir(parents=True)
    resource=resource/"fixture.txt"
    content=b"qualified long-path Git input\n"
    resource.write_bytes(content)
    relative=resource.relative_to(repository).as_posix()
    subprocess.run([git,"-C",str(repository),"add","--",relative],check=True,timeout=10)
    observed=subprocess.run([git,"-C",str(repository),"show",":"+relative],check=True,capture_output=True,timeout=10)
    if observed.stdout!=content:
        raise RuntimeError("Git did not preserve the actual long-path fixture bytes")
    inherited=subprocess.run([git,"-C",str(repository),"config","--get","alias.parent-scope-probe"],capture_output=True,timeout=10)
    if inherited.returncode!=1 or inherited.stdout:
        raise RuntimeError("Parent Git configuration crossed the isolated runtime boundary")
    print("Managed Git tracked and read a native path beyond 300 UTF-16 units")
'@
    [void](Invoke-Control 'git-long-path' @('python','-c',$gitPathProbe))
    [void](Invoke-Control 'exit-code' @('python','-c','raise SystemExit(7)') 7)
    $transport = Invoke-Control 'default-temp-git-transport' @('python','-m','pytest','-q','--no-cov','-o','addopts=','tests/test_ci_transport.py::test_frozen_trial_protocol_survives_lf_git_transport')
    if (-not $transport.Contains('1 passed')) { throw 'The default temporary location did not pass actual Git transport' }
    $timeout = Invoke-NativeControl 'timeout' @('-I','-S','-c','import time;time.sleep(30)') 1 1048576 'timeout'
    if ($timeout.exit_code -ne 124) { throw 'The timeout did not terminate its owned job' }
    $limited = Invoke-NativeControl 'output-limit' @('-I','-S','-c','import sys;sys.stdout.write("x"*1000000)') 10 1024 'output_limit'
    if ($limited.retained_output_bytes -ne 1024) { throw 'The output retention budget was exceeded' }
    $children = Invoke-NativeControl 'child-cleanup' @('-I','-S','-c','import subprocess,sys;child=subprocess.Popen([sys.executable,"-I","-S","-c","import time;time.sleep(30)"]);print(child.pid,flush=True)') 10 1048576 $null
    if ($children.exit_code -ne 0) { throw 'The owned child-process control failed' }
    $module = [IO.Path]::Combine($fresh.packages,'yaml/scanner.py')
    if (-not [IO.File]::Exists($module)) { throw 'The missing-dependency control requires the admitted module' }
    [IO.File]::Move($module,($module+'.qualification-original'))
    $repaired = (Invoke-Control 'missing-package-recovery' @('doctor')) | ConvertFrom-Json
    if (-not $repaired.newly_installed -or $repaired.packages -ceq $fresh.packages -or -not [IO.File]::Exists(($module+'.qualification-original'))) { throw 'Recovery did not preserve the original and provision a fresh environment' }

    $namespace = [IO.Directory]::GetParent($repaired.diagnostics).FullName
    $enginePointer = Join-Path $namespace 'tools/powershell.json'
    $oldEngine = [IO.File]::ReadAllText($enginePointer) | ConvertFrom-Json
    $oldEngineModule = Join-Path $oldEngine.home 'Microsoft.PowerShell.Commands.Utility.dll'
    if (-not $oldEngineModule.StartsWith(($namespace+[IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) { throw 'The missing-engine fixture escaped its owned namespace' }
    [IO.File]::Move($oldEngineModule,($oldEngineModule+'.qualification-original'))
    $engineRecovered = (Invoke-Control 'missing-engine-recovery' @('doctor')) | ConvertFrom-Json
    $newEngine = [IO.File]::ReadAllText($enginePointer) | ConvertFrom-Json
    if ($oldEngine.home -ceq $newEngine.home -or $engineRecovered.newly_installed -or -not [IO.File]::Exists(($oldEngineModule+'.qualification-original'))) { throw 'Missing engine recovery did not preserve the original and reuse the package environment' }
    $ordinaryEnginePointer = [IO.File]::ReadAllText($enginePointer)
    try {
        $extendedEnginePointer = $ordinaryEnginePointer | ConvertFrom-Json
        $extendedEnginePointer.home = '\\?\' + $extendedEnginePointer.home
        Write-Record $enginePointer $extendedEnginePointer
        $extendedEngine = (Invoke-Control 'extended-engine-path' @('doctor') 0 ('\\?\'+$cache)) | ConvertFrom-Json
        if (-not $extendedEngine.ready -or $extendedEngine.newly_installed) { throw 'The extended engine spelling was not resolved without changing the package environment' }
    } finally { [IO.File]::WriteAllText($enginePointer,$ordinaryEnginePointer,$utf8) }
    $sourceRecord = [IO.File]::ReadAllText((Join-Path $repaired.diagnostics 'source.json')) | ConvertFrom-Json
    $uvPointer = Join-Path $namespace 'tools/uv.json'
    $oldTool = [IO.File]::ReadAllText($uvPointer) | ConvertFrom-Json
    $oldUv = Join-Path $oldTool.home 'uv.exe'
    [IO.File]::Move($oldUv,($oldUv+'.qualification-original'))
    $restored = (Invoke-Control 'missing-tool-recovery' @('doctor')) | ConvertFrom-Json
    $newTool = [IO.File]::ReadAllText($uvPointer) | ConvertFrom-Json
    if ($oldTool.home -ceq $newTool.home -or $restored.newly_installed -or -not [IO.File]::Exists(($oldUv+'.qualification-original'))) { throw 'Missing tool recovery did not preserve the previous tool and package environment' }
    $unownedCache = Join-Path $output 'unowned-cache'
    $unownedNamespace = Join-Path $unownedCache ([IO.Path]::GetFileName($namespace))
    [void][IO.Directory]::CreateDirectory($unownedNamespace)
    $canary = Join-Path $unownedNamespace 'other-application.txt'
    [IO.File]::WriteAllText($canary,'must remain unchanged',$utf8)
    [void](Invoke-Control 'unowned-cache' @('doctor') 1 $unownedCache)
    if (-not ([IO.File]::ReadAllText((Join-Path $output 'unowned-cache.stderr.native'))).Contains('Refusing to adopt') -or [IO.File]::ReadAllText($canary) -cne 'must remain unchanged' -or @([IO.Directory]::EnumerateFileSystemEntries($unownedNamespace)).Count -ne 1) { throw 'The unowned cache was adopted or modified' }
    $pointer = Join-Path $namespace ('validation-'+$sourceRecord.graph_identity.Substring(0,16)+'.json')
    if (-not ([IO.Path]::GetFullPath($pointer)).StartsWith(($namespace+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'The concurrency fixture pointer escaped its owned cache' }
    [IO.File]::Move($pointer,($pointer+'.qualification-original'))
    $command = [string[]]@('-NoLogo','-NoProfile','-NonInteractive','-File',$entry,'--cache-root',$cache,'doctor')
    $pair = [BootstrapConcurrentQualification]::Run([SkillsBootstrap.OwnedProcess],(Process-Arguments 'concurrent-first' $command),(Process-Arguments 'concurrent-second' $command))
    foreach ($process in $pair) { if ($process.exit_code -ne 0 -or $null -ne $process.termination_reason -or $process.active_processes_after_cleanup -ne 0) { throw 'Concurrent callers failed ownership or readiness' } }
    $left = [IO.File]::ReadAllText((Join-Path $output 'concurrent-first.stdout.native')) | ConvertFrom-Json
    $right = [IO.File]::ReadAllText((Join-Path $output 'concurrent-second.stdout.native')) | ConvertFrom-Json
    if ($left.newly_installed -eq $right.newly_installed -or $left.packages -cne $right.packages) { throw 'Concurrent setup did not install once and reuse once' }
    $controls.Add(@{name='concurrent-installation'; processes=$pair; installed_once=$true})
    foreach ($name in $sourceNames) { if ($sources[$name] -cne (Get-FileHash -LiteralPath (Join-Path $root $name) -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'Qualification inputs changed during execution' } }
} catch { $failure = $_.Exception.ToString() }
finally {
    $after = Host-State
    Write-Record (Join-Path $output 'host-after.json') $after
    if (($before | ConvertTo-Json -Depth 16 -Compress) -cne ($after | ConvertTo-Json -Depth 16 -Compress)) { $failure = 'Persistent host PATH or Python/PowerShell registry changed' }
    Write-Record (Join-Path $output 'qualification.json') @{passed=($null -eq $failure); model_requests=0; source_root=$root; sources=$sources; cache_root=$cache; temporary_root=$privateTemporary; controls=$controls; failure=$failure}
}
Write-Output $output
if ($null -ne $failure) { throw $failure }
