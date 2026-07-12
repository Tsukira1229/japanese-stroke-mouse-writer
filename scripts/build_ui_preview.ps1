param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PackageName = "JapaneseStrokeMouseWriter-v2.6.0-preview.1-win-x64-portable"
$OutputRoot = Join-Path $Root "build\ui-preview"
$PackageDir = Join-Path $OutputRoot $PackageName
$WorkDir = Join-Path $Root "build\ui-preview-work"

Push-Location $Root
try {
    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
    $ResolvedOutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path
    if (Test-Path -LiteralPath $PackageDir) {
        $ResolvedPackageDir = (Resolve-Path -LiteralPath $PackageDir).Path
        if (-not $ResolvedPackageDir.StartsWith($ResolvedOutputRoot + "\", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected preview path: $ResolvedPackageDir"
        }
        Remove-Item -LiteralPath $ResolvedPackageDir -Recurse -Force
    }

    $env:JSMW_PACKAGE_NAME = $PackageName
    & $Python -m PyInstaller --noconfirm --clean `
        --distpath $OutputRoot `
        --workpath $WorkDir `
        "JapaneseStrokeMouseWriter.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller preview build failed." }

    Get-ChildItem -LiteralPath $Root -Filter "*.md" -File |
        Copy-Item -Destination $PackageDir -Force
    Copy-Item -LiteralPath (Join-Path $Root "LICENSE") -Destination $PackageDir -Force
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "user_data") -Force | Out-Null

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
    $SelfTestSettings = Join-Path $PackageDir "user_data\preview-self-test-settings.json"
    $SelfTest = Start-Process -FilePath $Executable `
        -ArgumentList "--self-test", "--settings-path", "`"$SelfTestSettings`"" `
        -WindowStyle Hidden -Wait -PassThru
    if ($SelfTest.ExitCode -ne 0) { throw "Frozen preview self-test failed." }
    Remove-Item -LiteralPath $SelfTestSettings -Force -ErrorAction SilentlyContinue

    Write-Output "Uncompressed UI preview: $PackageDir"
}
finally {
    Remove-Item Env:JSMW_PACKAGE_NAME -ErrorAction SilentlyContinue
    Pop-Location
}
