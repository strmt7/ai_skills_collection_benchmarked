param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$References,
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference='Stop'
$utf8=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=$utf8
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.dll')
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.CSharp.dll')
$text=[Microsoft.CodeAnalysis.Text.SourceText]::From([IO.File]::ReadAllText($Source,$utf8),$utf8,[Microsoft.CodeAnalysis.Text.SourceHashAlgorithm]::Sha256)
$parse=[Microsoft.CodeAnalysis.CSharp.CSharpParseOptions]::Default.WithLanguageVersion([Microsoft.CodeAnalysis.CSharp.LanguageVersion]::CSharp5)
$tree=[Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText($text,$parse,'/_/OwnedProcess.cs')
$metadata=New-Object 'System.Collections.Generic.List[Microsoft.CodeAnalysis.MetadataReference]'
foreach($name in @('mscorlib.dll','System.dll','System.Core.dll')) {
    $metadata.Add([Microsoft.CodeAnalysis.MetadataReference]::CreateFromFile((Join-Path $References $name)))
}
$options=[Microsoft.CodeAnalysis.CSharp.CSharpCompilationOptions]::new([Microsoft.CodeAnalysis.OutputKind]::DynamicallyLinkedLibrary)
$options=$options.WithDeterministic($true).WithOptimizationLevel([Microsoft.CodeAnalysis.OptimizationLevel]::Release).WithConcurrentBuild($false)
$compilation=[Microsoft.CodeAnalysis.CSharp.CSharpCompilation]::Create('SkillsBootstrap.NativeSupervisor',[Microsoft.CodeAnalysis.SyntaxTree[]]@($tree),[Microsoft.CodeAnalysis.MetadataReference[]]$metadata.ToArray(),$options)
$stream=New-Object IO.MemoryStream
try {
    $emitted=$compilation.Emit($stream)
    if(-not $emitted.Success){throw (($emitted.Diagnostics|ForEach-Object {$_.ToString()}) -join "`n")}
    [IO.File]::WriteAllBytes($Output,$stream.ToArray())
} finally {$stream.Dispose()}
@{runtime=$PSVersionTable.PSVersion.ToString();compiler=[Microsoft.CodeAnalysis.CSharp.CSharpCompilation].Assembly.GetName().Version.ToString();bytes=([IO.FileInfo]$Output).Length;sha256=(Get-FileHash -LiteralPath $Output -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json -Compress
