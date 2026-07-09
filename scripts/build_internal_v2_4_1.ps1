param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PackageName = "JapaneseStrokeMouseWriter-v2.4.1-win-x64-portable"
$Dist = Join-Path $Root "dist"
$PackageDir = Join-Path $Dist $PackageName
$VersionDir = Join-Path $Root "V2.4.1"
$InternalPortableDir = Join-Path $VersionDir $PackageName

Push-Location $Root
try {
    & $Python -m PyInstaller --noconfirm --clean "JapaneseStrokeMouseWriter.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

    Get-ChildItem -LiteralPath $Root -Filter "*.md" -File |
        Copy-Item -Destination $PackageDir -Force
    Copy-Item -LiteralPath (Join-Path $Root "LICENSE") -Destination $PackageDir -Force
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "user_data") -Force | Out-Null

    $Executable = Join-Path $PackageDir "JapaneseStrokeMouseWriter.exe"
    $SelfTestSettings = Join-Path $PackageDir "user_data\self-test-settings.json"
    $SelfTest = Start-Process -FilePath $Executable `
        -ArgumentList "--self-test", "--settings-path", "`"$SelfTestSettings`"" `
        -WindowStyle Hidden -Wait -PassThru
    if ($SelfTest.ExitCode -ne 0) { throw "Frozen executable self-test failed." }
    Remove-Item -LiteralPath $SelfTestSettings -Force -ErrorAction SilentlyContinue

    if (Test-Path -LiteralPath $InternalPortableDir) {
        $ResolvedTarget = (Resolve-Path -LiteralPath $InternalPortableDir).Path
        $ResolvedVersionDir = (Resolve-Path -LiteralPath $VersionDir).Path
        if (-not $ResolvedTarget.StartsWith($ResolvedVersionDir, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove unexpected path: $ResolvedTarget"
        }
        Remove-Item -LiteralPath $InternalPortableDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $VersionDir -Force | Out-Null
    Copy-Item -LiteralPath $PackageDir -Destination $InternalPortableDir -Recurse -Force

    Write-Output "Internal portable folder: $InternalPortableDir"
}
finally {
    Pop-Location
}
