param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PackageName = "JapaneseStrokeMouseWriter-v2.0.2-win-x64-portable"
$Dist = Join-Path $Root "dist"
$PackageDir = Join-Path $Dist $PackageName
$Archive = Join-Path $Dist "$PackageName.zip"
$HashFile = Join-Path $Dist "$PackageName.zip.sha256"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

Push-Location $Root
try {
    & $Python -m PyInstaller --noconfirm --clean "JapaneseStrokeMouseWriter.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

    Get-ChildItem -LiteralPath $Root -Filter "*.md" -File |
        Copy-Item -Destination $PackageDir -Force
    New-Item -ItemType Directory -Path (Join-Path $PackageDir "user_data") -Force | Out-Null

    $Executable = Join-Path $PackageDir "JapaneseStrokeMouseWriter.exe"
    $SelfTestSettings = Join-Path $PackageDir "user_data\self-test-settings.json"
    $SelfTest = Start-Process -FilePath $Executable `
        -ArgumentList "--self-test", "--settings-path", "`"$SelfTestSettings`"" `
        -WindowStyle Hidden -Wait -PassThru
    if ($SelfTest.ExitCode -ne 0) { throw "Frozen executable self-test failed." }
    Remove-Item -LiteralPath $SelfTestSettings -Force -ErrorAction SilentlyContinue

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
