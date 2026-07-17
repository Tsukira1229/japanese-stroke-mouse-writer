param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PackageName = "JapaneseStrokeMouseWriter-v2.7.0-win-x64-portable"
$Dist = Join-Path $Root "dist"
$PackageDir = Join-Path $Dist $PackageName
$Archive = Join-Path $Dist "$PackageName.zip"
$HashFile = Join-Path $Dist "$PackageName.zip.sha256"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Assert-StrokeStylePackIdentity {
    param([Parameter(Mandatory = $true)][string]$CandidateRoot)

    $SourceRoot = Join-Path $Root "data\stroke_styles"
    if (-not (Test-Path -LiteralPath $CandidateRoot -PathType Container)) {
        throw "Packaged stroke-style root is missing: $CandidateRoot"
    }
    $SourceFiles = @(Get-ChildItem -LiteralPath $SourceRoot -Recurse -File)
    $CandidateFiles = @(Get-ChildItem -LiteralPath $CandidateRoot -Recurse -File)
    if ($SourceFiles.Count -ne $CandidateFiles.Count) {
        throw "Packaged stroke-style file count differs from source."
    }
    foreach ($SourceFile in $SourceFiles) {
        if (-not $SourceFile.FullName.StartsWith($SourceRoot + "\", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Unexpected source stroke-style path: $($SourceFile.FullName)"
        }
        $Relative = $SourceFile.FullName.Substring($SourceRoot.Length).TrimStart("\")
        $Candidate = Join-Path $CandidateRoot $Relative
        if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) {
            throw "Packaged stroke-style file is missing: $Relative"
        }
        $SourceHash = (Get-FileHash -LiteralPath $SourceFile.FullName -Algorithm SHA256).Hash
        $CandidateHash = (Get-FileHash -LiteralPath $Candidate -Algorithm SHA256).Hash
        if ($SourceHash -ne $CandidateHash) {
            throw "Packaged stroke-style file differs from source: $Relative"
        }
    }
}

Push-Location $Root
try {
    & $Python "scripts/generate_html_guides.py" --check
    if ($LASTEXITCODE -ne 0) { throw "HTML guides are not up to date." }

    & $Python -m PyInstaller --noconfirm --clean "JapaneseStrokeMouseWriter.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

    Get-ChildItem -LiteralPath $Root -Filter "*.md" -File |
        Copy-Item -Destination $PackageDir -Force
    Get-ChildItem -LiteralPath $Root -Filter "*.html" -File |
        Copy-Item -Destination $PackageDir -Force
    Copy-Item -LiteralPath (Join-Path $Root "LICENSE") -Destination $PackageDir -Force
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "user_data") -Force | Out-Null

    $MatplotlibSampleData = Join-Path $PackageDir "_internal\matplotlib\mpl-data\sample_data"
    if (Test-Path -LiteralPath $MatplotlibSampleData) {
        $ResolvedSampleData = (Resolve-Path -LiteralPath $MatplotlibSampleData).Path
        $ResolvedPackageDir = (Resolve-Path -LiteralPath $PackageDir).Path
        if (-not $ResolvedSampleData.StartsWith($ResolvedPackageDir + "\", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected path: $ResolvedSampleData"
        }
        Remove-Item -LiteralPath $ResolvedSampleData -Recurse -Force
    }

    $Executable = Join-Path $PackageDir "JapaneseStrokeMouseWriter.exe"
    $SelfTestSettings = Join-Path $PackageDir "user_data\self-test-settings.json"
    $SelfTest = Start-Process -FilePath $Executable `
        -ArgumentList "--self-test", "--settings-path", "`"$SelfTestSettings`"" `
        -WindowStyle Hidden -Wait -PassThru
    if ($SelfTest.ExitCode -ne 0) { throw "Frozen executable self-test failed." }
    Remove-Item -LiteralPath $SelfTestSettings -Force -ErrorAction SilentlyContinue
    Assert-StrokeStylePackIdentity (Join-Path $PackageDir "_internal\data\stroke_styles")

    Remove-Item -LiteralPath $Archive -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $HashFile -Force -ErrorAction SilentlyContinue
    [IO.Compression.ZipFile]::CreateFromDirectory(
        $PackageDir,
        $Archive,
        [IO.Compression.CompressionLevel]::Optimal,
        $true
    )

    $VerifyDir = Join-Path $env:TEMP ("jsmw-v2-verify-" + [guid]::NewGuid().ToString("N"))
    try {
        [IO.Compression.ZipFile]::ExtractToDirectory($Archive, $VerifyDir)
        $Extracted = Join-Path $VerifyDir $PackageName
        $ExtractedExe = Join-Path $Extracted "JapaneseStrokeMouseWriter.exe"
        $VerifySettings = Join-Path $Extracted "user_data\verify-settings.json"
        $ExtractedTest = Start-Process -FilePath $ExtractedExe `
            -ArgumentList "--self-test", "--settings-path", "`"$VerifySettings`"" `
            -WindowStyle Hidden -Wait -PassThru
        if ($ExtractedTest.ExitCode -ne 0) { throw "Extracted portable self-test failed." }
        Assert-StrokeStylePackIdentity (Join-Path $Extracted "_internal\data\stroke_styles")
    }
    finally {
        if (Test-Path -LiteralPath $VerifyDir) {
            Remove-Item -LiteralPath $VerifyDir -Recurse -Force
        }
    }

    $Hash = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
    "$Hash  $PackageName.zip" | Set-Content -LiteralPath $HashFile -Encoding ascii
    Write-Output "Portable archive: $Archive"
    Write-Output "SHA-256: $Hash"
}
finally {
    Pop-Location
}

