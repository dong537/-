param(
  [int]$ApiPort = 8010,
  [int]$WebPort = 5173
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiScript = Join-Path $Root "scripts\start-api.ps1"
$WebScript = Join-Path $Root "scripts\start-web.ps1"
$ApiLog = Join-Path $Root "api\server-real-device.out.log"
$ApiErr = Join-Path $Root "api\server-real-device.err.log"
$WebLog = Join-Path $Root "web\server-dev.out.log"
$WebErr = Join-Path $Root "web\server-dev.err.log"

$ipCandidates = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object {
    $_.IPAddress -notlike "127.*" -and
    $_.IPAddress -notlike "169.254.*" -and
    $_.PrefixOrigin -ne "WellKnown"
  } |
  Sort-Object InterfaceMetric, InterfaceIndex

$primaryIp = ($ipCandidates | Select-Object -First 1).IPAddress
if (-not $primaryIp) {
  $primaryIp = "127.0.0.1"
}

$env:APP_BASE_URL = "http://$primaryIp`:$ApiPort"
$env:INSTA360_NATIVE_BRIDGE_ENABLED = "true"

Start-Process -FilePath "powershell.exe" -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  $ApiScript,
  "-Port",
  "$ApiPort",
  "-BindHost",
  "0.0.0.0"
) -WindowStyle Hidden -RedirectStandardOutput $ApiLog -RedirectStandardError $ApiErr

Start-Process -FilePath "powershell.exe" -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  $WebScript,
  "-Port",
  "$WebPort"
) -WindowStyle Hidden -RedirectStandardOutput $WebLog -RedirectStandardError $WebErr

Start-Sleep -Seconds 4

Write-Host "Panorama Companion is starting in real-device mode."
Write-Host "Web: http://127.0.0.1:$WebPort"
Write-Host "API local: http://127.0.0.1:$ApiPort"
Write-Host "API for Android phone: http://$primaryIp`:$ApiPort"
Write-Host "Set the Android bridge API URL to: http://$primaryIp`:$ApiPort"
Write-Host "Logs:"
Write-Host "  $ApiLog"
Write-Host "  $ApiErr"
Write-Host "  $WebLog"
Write-Host "  $WebErr"
