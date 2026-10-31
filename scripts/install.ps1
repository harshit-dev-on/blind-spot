# One-command Windows installer. Supports running from GitHub or from a local checkout.
# irm https://raw.githubusercontent.com/harshit-dev-on/blind-spot/master/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$BlindSpotHome = Join-Path $HOME ".blindspot"
$InstallDir = Join-Path $BlindSpotHome "bin"
$VenvDir = Join-Path $BlindSpotHome "venv-py312"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$UvInstallDir = Join-Path $BlindSpotHome "uv"

New-Item -ItemType Directory -Force -Path $InstallDir, $BlindSpotHome | Out-Null

$UvCommand = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($UvCommand) {
    $Uv = $UvCommand.Path
} else {
    Write-Host "Installing the managed Python/package installer..." -ForegroundColor Cyan
    $env:UV_INSTALL_DIR = $UvInstallDir
    $env:UV_NO_MODIFY_PATH = "1"
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $Uv = Join-Path $UvInstallDir "uv.exe"
    if (-not (Test-Path -LiteralPath $Uv)) {
        throw "The Python bootstrapper did not install uv at $Uv"
    }
}

function Invoke-Uv {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$UvArgs)
    & $Uv @UvArgs
    if ($LASTEXITCODE -ne 0) {
        throw "uv failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Installing Python 3.12 and creating an isolated environment..." -ForegroundColor Cyan
Invoke-Uv python install 3.12
Invoke-Uv venv --clear --python 3.12 $VenvDir

$RepoRoot = $null
if ($PSScriptRoot -and (Test-Path -LiteralPath (Join-Path $PSScriptRoot "..\pyproject.toml"))) {
    $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

Write-Host "Installing BlindSpot and its Python dependencies..." -ForegroundColor Cyan
if ($RepoRoot) {
    Invoke-Uv pip install --python $VenvPython --upgrade --editable $RepoRoot
} else {
    $ZipUrl = "https://github.com/harshit-dev-on/blind-spot/archive/refs/heads/main.zip"
    try {
        $check = Invoke-WebRequest -Uri $ZipUrl -Method Head -ErrorAction SilentlyContinue
        if ($check.StatusCode -ne 200) {
            $ZipUrl = "https://github.com/harshit-dev-on/blind-spot/archive/refs/heads/master.zip"
        }
    } catch {
        $ZipUrl = "https://github.com/harshit-dev-on/blind-spot/archive/refs/heads/master.zip"
    }
    Invoke-Uv pip install --python $VenvPython --upgrade $ZipUrl
}

Write-Host "Installing the Chromium browser..." -ForegroundColor Cyan
& $VenvPython -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    throw "Playwright could not install Chromium. Re-run the installer after checking your network connection."
}

$ShimContent = "@echo off`r`n`"$VenvPython`" -m blindspot1 %*`r`n"
foreach ($CommandName in @("blindspot.cmd", "blindspot1.cmd")) {
    [System.IO.File]::WriteAllText((Join-Path $InstallDir $CommandName), $ShimContent, [System.Text.Encoding]::ASCII)
}

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$PathEntries = @($UserPath -split ";" | Where-Object { $_ })
if ($PathEntries -notcontains $InstallDir) {
    $UpdatedPath = (@($InstallDir) + $PathEntries) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $UpdatedPath, "User")
}
if (($env:Path -split ";") -notcontains $InstallDir) {
    $env:Path = "$InstallDir;$env:Path"
}

Write-Host "Configuring global Antigravity plugin and skills..." -ForegroundColor Cyan
try {
    & $VenvPython -m blindspot1 skill install --global
} catch {
    Write-Warning "Could not configure global Antigravity plugin automatically: $_"
}

Write-Host "`nBlindSpot is installed." -ForegroundColor Green
Write-Host "Run 'blindspot1 setup' any time to change providers or model settings."
Write-Host "The default Antigravity mode works without a cloud API key."

$UserConfig = Join-Path $BlindSpotHome "config.toml"
if (-not (Test-Path -LiteralPath $UserConfig)) {
    Write-Host "`nLet's configure your first run. Choose the Antigravity default for a no-key setup." -ForegroundColor Cyan
    & $VenvPython -m blindspot1 setup
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Installation completed. Run 'blindspot1 setup' to finish configuration."
    }
} else {
    Write-Host "Existing configuration found at $UserConfig; it was left unchanged."
}

Write-Host "`nStart an audit with: blindspot live `"https://example.com`"" -ForegroundColor Yellow
Write-Host "If this terminal cannot find the command, open a new PowerShell window."
