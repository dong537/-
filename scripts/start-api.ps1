param(
  [int]$Port = 8010,
  [string]$BindHost = "127.0.0.1"
)

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
& $Python -m uvicorn app.main:app --reload --host $BindHost --port $Port
Pop-Location
