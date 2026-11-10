function Assert-CabinetInventory($Actual,$Expected) {
    $names=@($Expected.psobject.Properties.Name)
    if($Actual.Count -ne $names.Count) { throw 'Native cabinet member count differs from its complete pin' }
    foreach($entry in $Actual) {
        if($names -cnotcontains $entry.name -or $Expected.($entry.name).bytes -ne $entry.bytes) { throw 'Native cabinet inventory differs from its complete pin' }
    }
}
function Assert-PinnedFiles([string]$PayloadRoot,$Expected) {
    foreach($entry in $Expected.psobject.Properties) {
        $file=Join-Path $PayloadRoot $entry.Name
        Assert-OrdinaryPath $file
        if(-not [IO.File]::Exists((Native-Path $file)) -or [IO.FileInfo]::new((Native-Path $file)).Length -ne $entry.Value.bytes -or (Get-Digest (Native-Path $file)) -cne $entry.Value.sha256) { throw 'Extracted native file differs from its exact qualified source' }
    }
}
function Expand-PinnedTar([string]$ArchivePath,[string]$PayloadRoot,$Pin) {
    Add-Type -AssemblyName System.Formats.Tar
    $expected=@($Pin.files.psobject.Properties.Name)
    $seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $count=0
    $stream=[IO.File]::OpenRead((Native-Path $ArchivePath))
    $gzip=$null; $reader=$null
    try {
        $gzip=[IO.Compression.GZipStream]::new($stream,[IO.Compression.CompressionMode]::Decompress,$true)
        $reader=[System.Formats.Tar.TarReader]::new($gzip,$true)
        while ($null -ne ($entry=$reader.GetNextEntry($false))) {
            $name=$entry.Name
            if ($name -match '(^/|[\\:]|(^|/)\.\.?(/|$))' -or -not $seen.Add($name)) { throw 'Pinned tar contains a noncanonical or duplicate path' }
            if ([string]$entry.EntryType -eq 'Directory') {
                $prefix=$name.TrimEnd('/')+'/'
                if (-not @($expected | Where-Object { $_.StartsWith($prefix,[StringComparison]::Ordinal) }).Count) { throw 'Pinned tar contains an undeclared directory' }
                continue
            }
            if ([string]$entry.EntryType -notin @('RegularFile','V7RegularFile') -or $expected -cnotcontains $name) { throw 'Pinned tar contains an undeclared member or unsupported type' }
            $declared=$Pin.files.$name
            if ($entry.Length -ne $declared.bytes) { throw 'Pinned tar member size differs' }
            $target=[IO.Path]::Combine($PayloadRoot,$name.Replace('/','\'))
            Assert-OrdinaryPath $target
            [void][IO.Directory]::CreateDirectory((Native-Path ([IO.Path]::GetDirectoryName($target))))
            $file=[IO.File]::Open((Native-Path $target),[IO.FileMode]::CreateNew)
            try {
                if ($null -ne $entry.DataStream) { $entry.DataStream.CopyTo($file) }
            } finally { $file.Dispose() }
            if ([IO.FileInfo]::new((Native-Path $target)).Length -ne $declared.bytes -or (Get-Digest (Native-Path $target)) -cne $declared.sha256) { throw 'Pinned tar member integrity differs' }
            $count++
        }
        if ($count -ne $expected.Count) { throw 'Pinned tar is missing declared files' }
    } finally {
        if ($null -ne $reader) { $reader.Dispose() }
        if ($null -ne $gzip) { $gzip.Dispose() }
        $stream.Dispose()
    }
}
function Expand-QualifiedPayload([string]$ArchivePath,[string]$PayloadRoot,$Pin) {
    if ($Pin.format -eq 'npm-tar-gzip') {
        Expand-PinnedTar $ArchivePath $PayloadRoot $Pin
        return $PayloadRoot
    }
    if($Pin.format -eq 'microsoft-cabinet') {
        $work=Join-Path $temporary ('crt-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
        Assert-OrdinaryPath $work
        [void][IO.Directory]::CreateDirectory($work)
        Write-Json (Join-Path $work 'owner.json') @{purpose='qualified-vendor-cabinet-extraction';diagnostics=$logs}
        $raw=[IO.File]::ReadAllBytes((Native-Path $ArchivePath))
        $offset=[long]$Pin.cabinet.offset; $length=[long]$Pin.cabinet.bytes
        if($offset -lt 0 -or $length -lt 36 -or $length -gt 33554432 -or $offset+$length -gt $raw.Length) { throw 'Pinned cabinet byte range is outside its qualified bundle' }
        $content=New-Object byte[] $length
        [Buffer]::BlockCopy($raw,$offset,$content,0,$length)
        $cabinet=Join-Path $work 'outer.cab'
        [IO.File]::WriteAllBytes($cabinet,$content)
        if((Get-Digest $cabinet) -cne $Pin.cabinet.sha256) { throw 'Pinned cabinet range integrity differs' }
        $outer=Join-Path $work 'outer'
        $members=@([SkillsBootstrap.NativeCabinet]::Read($cabinet,$outer,$false))
        Assert-CabinetInventory $members $Pin.outer_files
        [void][SkillsBootstrap.NativeCabinet]::Read($cabinet,$outer,$true)
        Assert-PinnedFiles $outer $Pin.outer_files
        if($Pin.inner_member -cne 'a4') { throw 'The qualified x64 minimum runtime member changed' }
        $inner=Join-Path $outer $Pin.inner_member
        $expanded=Join-Path $work 'minimum'
        $members=@([SkillsBootstrap.NativeCabinet]::Read($inner,$expanded,$false))
        Assert-CabinetInventory $members $Pin.native_files
        [void][SkillsBootstrap.NativeCabinet]::Read($inner,$expanded,$true)
        Assert-PinnedFiles $expanded $Pin.native_files
        foreach($entry in $Pin.native_files.psobject.Properties) {
            $name=$entry.Name
            if(-not $name.EndsWith('.dll_amd64',[StringComparison]::Ordinal) -or [IO.Path]::GetFileName($name) -cne $name) { throw 'The native x64 file mapping changed' }
            $target=$name.Substring(0,$name.Length-6)
            if(@($Pin.files.psobject.Properties.Name) -cnotcontains $target -or $Pin.files.$target.sha256 -cne $entry.Value.sha256) { throw 'The native runtime mapping differs from its exact file pin' }
            $source=Join-Path $expanded $name
            $bytes=[IO.File]::ReadAllBytes($source)
            if($bytes.Length -lt 64 -or $bytes[0] -ne 77 -or $bytes[1] -ne 90) { throw 'Native runtime has no PE header' }
            $pe=[BitConverter]::ToInt32($bytes,60)
            if($pe -lt 64 -or $pe+6 -gt $bytes.Length -or [BitConverter]::ToUInt32($bytes,$pe) -ne 0x4550 -or [BitConverter]::ToUInt16($bytes,$pe+4) -ne 0x8664) { throw 'Native runtime architecture differs from Windows x64' }
            if([Diagnostics.FileVersionInfo]::GetVersionInfo($source).FileVersion -cne $Pin.version) { throw 'Native runtime version differs from its admitted vendor bundle' }
            [IO.File]::Copy($source,(Native-Path (Join-Path $PayloadRoot $target)))
        }
        return $PayloadRoot
    }
    if($Pin.format -eq 'tar-gzip') {
        if([string]::IsNullOrEmpty($archivePython)) { throw 'A qualified archive interpreter is required before this payload' }
        $payload=Join-Path $PayloadRoot 'payload'
        $arguments=@('-I','-B','-X','utf8',(Join-Path $rootPath 'tools/_bootstrap_archive.py'),'--archive',(Native-Path $ArchivePath),'--manifest',(Join-Path $bootstrapHome 'manifest.json'),'--python',$Pin.version,'--output',(Native-Path $payload))
        [void](Invoke-Owned 'python-archive' $archivePython $arguments)
        if($Pin.native_layer -cne 'microsoft_runtime') { throw 'The qualified Python native layer changed' }
        $native=Ensure-Tool 'microsoft-runtime' $manifest.microsoft_runtime $toolRoot
        $originals=Join-Path $PayloadRoot 'original-runtime-files'
        [void][IO.Directory]::CreateDirectory((Native-Path $originals))
        foreach($entry in $manifest.microsoft_runtime.files.psobject.Properties) {
            $destination=Join-Path $payload $entry.Name
            Assert-OrdinaryPath $destination
            if([IO.File]::Exists((Native-Path $destination))) { [IO.File]::Copy((Native-Path $destination),(Native-Path (Join-Path $originals $entry.Name))) }
            [IO.File]::Copy((Native-Path (Join-Path $native $entry.Name)),(Native-Path $destination),$true)
        }
        Assert-PinnedFiles $payload $Pin.files
        return $payload
    }
    throw 'Unsupported pinned archive format'
}
