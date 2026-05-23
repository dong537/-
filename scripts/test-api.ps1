$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiDir = Join-Path $Root "api"
$Python = Join-Path $ApiDir ".venv\Scripts\python.exe"

if (!(Test-Path $Python)) {
  Push-Location $ApiDir
  python -m venv .venv
  & $Python -m pip install -r requirements.txt
  Pop-Location
}

Push-Location $ApiDir
& $Python -m pip install -r requirements-dev.txt
& $Python -m ruff check app tests
& $Python -m pytest
Pop-Location
