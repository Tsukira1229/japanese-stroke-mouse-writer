param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PackageName = "JapaneseStrokeMouseWriter-v2.7.1-development-win-x64-portable"
$OutputRoot = Join-Path $Root "build\development-v2.7.1"
$PackageDir = Join-Path $OutputRoot $PackageName
$WorkDir = Join-Path $Root ("build\development-v2.7.1-work-" + [guid]::NewGuid().ToString("N"))

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Parent,
        [Parameter(Mandatory = $true)][string]$Child
    )

    $ResolvedParent = (Resolve-Path -LiteralPath $Parent).Path
    $ResolvedChild = (Resolve-Path -LiteralPath $Child).Path
    if (-not $ResolvedChild.StartsWith($ResolvedParent + "\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unexpected path outside development output: $ResolvedChild"
    }
}

Push-Location $Root
try {
    & $Python "scripts/generate_html_guides.py" --check
    if ($LASTEXITCODE -ne 0) { throw "HTML guides are not up to date." }

    New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
    if (Test-Path -LiteralPath $PackageDir) {
        Assert-ChildPath -Parent $OutputRoot -Child $PackageDir
        Remove-Item -LiteralPath $PackageDir -Recurse -Force
    }

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
    @(
        "Japanese Stroke Mouse Writer V2.7.1 Development"
        "Internal uncompressed build. Not a GitHub Release."
        "The bundled executable is unsigned."
    ) | Set-Content -LiteralPath (Join-Path $PackageDir "DEVELOPMENT_BUILD.txt") -Encoding utf8

    $MatplotlibSampleData = Join-Path $PackageDir "_internal\matplotlib\mpl-data\sample_data"
    if (Test-Path -LiteralPath $MatplotlibSampleData) {
        Assert-ChildPath -Parent $PackageDir -Child $MatplotlibSampleData
        Remove-Item -LiteralPath $MatplotlibSampleData -Recurse -Force
    }

    foreach ($StyleId in @("yomogi", "zen-kurenaido", "hachi-maru-pop")) {
        foreach ($ArchiveName in @("strokes.zip", "orders.zip")) {
            $SourceStyle = Join-Path $Root "data\stroke_styles\$StyleId\$ArchiveName"
            $PackagedStyle = Join-Path $PackageDir "_internal\data\stroke_styles\$StyleId\$ArchiveName"
            if (-not (Test-Path -LiteralPath $PackagedStyle -PathType Leaf)) {
                throw "Packaged style archive is missing: $StyleId/$ArchiveName"
            }
            if ((Get-FileHash -LiteralPath $SourceStyle -Algorithm SHA256).Hash -ne
                (Get-FileHash -LiteralPath $PackagedStyle -Algorithm SHA256).Hash) {
                throw "Packaged style archive differs from the source pack: $StyleId/$ArchiveName"
            }
        }
    }

    $Executable = Join-Path $PackageDir "JapaneseStrokeMouseWriter.exe"
    $SelfTestSettings = Join-Path $PackageDir "user_data\development-self-test-settings.json"
    $SelfTest = Start-Process -FilePath $Executable `
        -ArgumentList "--self-test", "--settings-path", "`"$SelfTestSettings`"" `
        -WindowStyle Hidden -Wait -PassThru
    if ($SelfTest.ExitCode -ne 0) { throw "Frozen development self-test failed." }
    Remove-Item -LiteralPath $SelfTestSettings -Force -ErrorAction SilentlyContinue

    if (Get-ChildItem -LiteralPath $OutputRoot -Filter "*.zip" -File) {
        throw "An unexpected outer ZIP was created in the development output."
    }
    Write-Output "Uncompressed V2.7.1 development build: $PackageDir"
}
finally {
    Remove-Item Env:JSMW_PACKAGE_NAME -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $WorkDir) {
        $BuildRoot = Join-Path $Root "build"
        Assert-ChildPath -Parent $BuildRoot -Child $WorkDir
        Remove-Item -LiteralPath $WorkDir -Recurse -Force
    }
    Pop-Location
}
