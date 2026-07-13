param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PackageName = "JapaneseStrokeMouseWriter-v2.6.1-development-win-x64-portable"
$OutputRoot = Join-Path $Root "build\development-v2.6.1"
$PackageDir = Join-Path $OutputRoot $PackageName
$WorkDir = Join-Path $Root "build\development-v2.6.1-work"

Push-Location $Root
try {
    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
    $ResolvedOutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path
    if (Test-Path -LiteralPath $PackageDir) {
        $ResolvedPackageDir = (Resolve-Path -LiteralPath $PackageDir).Path
        if (-not $ResolvedPackageDir.StartsWith($ResolvedOutputRoot + "\", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected development-build path: $ResolvedPackageDir"
        }
        Remove-Item -LiteralPath $ResolvedPackageDir -Recurse -Force
    }

    & $Python "scripts/generate_html_guides.py" --check
    if ($LASTEXITCODE -ne 0) { throw "HTML guides are not up to date." }

    $env:JSMW_PACKAGE_NAME = $PackageName
    & $Python -m PyInstaller --noconfirm --clean `
        --distpath $OutputRoot `
        --workpath $WorkDir `
        "JapaneseStrokeMouseWriter.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller development build failed." }

    Get-ChildItem -LiteralPath $Root -Filter "*.md" -File |
        Copy-Item -Destination $PackageDir -Force
    Get-ChildItem -LiteralPath $Root -Filter "*.html" -File |
        Copy-Item -Destination $PackageDir -Force
    Copy-Item -LiteralPath (Join-Path $Root "LICENSE") -Destination $PackageDir -Force
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "user_data") -Force | Out-Null

    @"
Japanese Stroke Mouse Writer V2.6.1 Development Build

Status: Internal development build; this folder is not a GitHub Release.
Signing: Unsigned.
Includes: coordinate-detection crosshairs, start-position reference display,
and synchronized Unicode special-symbol SVG mappings.
"@ | Set-Content -LiteralPath (Join-Path $PackageDir "DEVELOPMENT_BUILD.txt") -Encoding utf8

    $MatplotlibSampleData = Join-Path $PackageDir "_internal\matplotlib\mpl-data\sample_data"
    if (Test-Path -LiteralPath $MatplotlibSampleData) {
        $ResolvedSampleData = (Resolve-Path -LiteralPath $MatplotlibSampleData).Path
        $ResolvedPackageDir = (Resolve-Path -LiteralPath $PackageDir).Path
        if (-not $ResolvedSampleData.StartsWith($ResolvedPackageDir + "\", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected sample-data path: $ResolvedSampleData"
        }
        Remove-Item -LiteralPath $ResolvedSampleData -Recurse -Force
    }

    $Executable = Join-Path $PackageDir "JapaneseStrokeMouseWriter.exe"
    $SelfTestSettings = Join-Path $PackageDir "user_data\development-self-test-settings.json"
    $SelfTest = Start-Process -FilePath $Executable `
        -ArgumentList "--self-test", "--settings-path", "`"$SelfTestSettings`"" `
        -WindowStyle Hidden -Wait -PassThru
    if ($SelfTest.ExitCode -ne 0) { throw "Frozen development-build self-test failed." }
    Remove-Item -LiteralPath $SelfTestSettings -Force -ErrorAction SilentlyContinue

    $SourceStrokeDir = Join-Path $Root "data\custom_strokes"
    $PackagedStrokeDir = Join-Path $PackageDir "_internal\data\custom_strokes"
    $SourceStrokes = @(Get-ChildItem -LiteralPath $SourceStrokeDir -Filter "*.svg" -File)
    $PackagedStrokes = @(Get-ChildItem -LiteralPath $PackagedStrokeDir -Filter "*.svg" -File)
    if ($SourceStrokes.Count -ne $PackagedStrokes.Count) {
        throw "Packaged custom-stroke count does not match the source."
    }
    foreach ($SourceStroke in $SourceStrokes) {
        $PackagedStroke = Join-Path $PackagedStrokeDir $SourceStroke.Name
        if (-not (Test-Path -LiteralPath $PackagedStroke)) {
            throw "Packaged SVG is missing: $($SourceStroke.Name)"
        }
        $SourceHash = (Get-FileHash -LiteralPath $SourceStroke.FullName -Algorithm SHA256).Hash
        $PackagedHash = (Get-FileHash -LiteralPath $PackagedStroke -Algorithm SHA256).Hash
        if ($SourceHash -ne $PackagedHash) {
            throw "Packaged SVG differs from source: $($SourceStroke.Name)"
        }
    }

    $SourceManifest = Join-Path $Root "data\symbol_manifest.json"
    $PackagedManifest = Join-Path $PackageDir "_internal\data\symbol_manifest.json"
    if ((Get-FileHash -LiteralPath $SourceManifest -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $PackagedManifest -Algorithm SHA256).Hash) {
        throw "Packaged symbol manifest differs from source."
    }

    Write-Output "Uncompressed V2.6.1 development build: $PackageDir"
    Write-Output "Verified custom SVG files: $($SourceStrokes.Count)"
    Write-Output "No ZIP, tag, or GitHub Release was created."
}
finally {
    Remove-Item Env:JSMW_PACKAGE_NAME -ErrorAction SilentlyContinue
    Pop-Location
}
