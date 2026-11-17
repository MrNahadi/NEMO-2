# Installs or repairs NEMO on Windows. Run through "Install NEMO.bat".
# Needs an internet connection the first time. Safe to run again.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($text) { Write-Host ""; Write-Host "==> $text" -ForegroundColor Cyan }
function Fail($text) {
    Write-Host ""
    Write-Host "NEMO could not be installed: $text" -ForegroundColor Red
    exit 1
}

Step "Checking for uv (the tool that downloads Python for NEMO)"
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    $local = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (Test-Path $local) {
        $uv = $local
    } else {
        Write-Host "Downloading uv from astral.sh ..."
        try {
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        } catch {
            Fail "uv could not be downloaded. Check the internet connection and try again."
        }
        $uv = $local
    }
} else {
    $uv = $uv.Source
}
if (-not (Test-Path $uv)) { Fail "uv was not found after downloading it." }

Step "Getting Python 3.12 for NEMO (this does not change any other Python on this computer)"
& $uv python install 3.12
if ($LASTEXITCODE -ne 0) { Fail "Python 3.12 could not be downloaded." }

Step "Creating NEMO's private Python environment"
$venv = Join-Path $root "engine\.venv"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    & $uv venv $venv --python 3.12
    if ($LASTEXITCODE -ne 0) { Fail "The Python environment could not be created." }
}
$python = Join-Path $venv "Scripts\python.exe"

Step "Installing the NEMO engine (about 300 MB the first time)"
& $uv pip install --python $python -e (Join-Path $root "engine")
if ($LASTEXITCODE -ne 0) { Fail "The NEMO engine could not be installed." }

Step "Checking the app files"
$index = Join-Path $root "app\dist\index.html"
if (-not (Test-Path $index)) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) {
        Fail "The app files (app\dist) are missing and Node.js is not installed to build them. Use a NEMO download that includes the app."
    }
    Push-Location (Join-Path $root "app")
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "The app's packages could not be installed." }
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "The app could not be built." }
    Pop-Location
}

Step "Testing the installation"
& $python -c "import nemo, build123d, gmsh, skfem, fastapi; print('NEMO engine', nemo.__version__, 'is ready')"
if ($LASTEXITCODE -ne 0) { Fail "The engine did not start. Run Install NEMO again." }

Step "Adding a NEMO shortcut to the desktop"
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $desktop "NEMO.lnk"))
$link.TargetPath = Join-Path $root "Start NEMO.bat"
$link.WorkingDirectory = $root
$link.Description = "Start NEMO"
$link.Save()

Write-Host ""
Write-Host "NEMO is installed. Double-click the NEMO shortcut on your desktop to start it." -ForegroundColor Green
