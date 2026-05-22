param(
  [int]$Port = 5173
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$WebDir = Join-Path $Root "web"
$Npm = "C:\Program Files\nodejs\npm.cmd"

if (!(Test-Path $Npm)) {
  $Npm = "npm"
}

Push-Location $WebDir
if (!(Test-Path "node_modules")) {
  & $Npm install
}
& $Npm run dev -- --host 127.0.0.1 --port $Port
Pop-Location
