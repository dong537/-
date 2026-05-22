$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$ApiScript = Join-Path $Root "scripts\start-api.ps1"
$WebScript = Join-Path $Root "scripts\start-web.ps1"
$ApiLog = Join-Path $Root "api\server-dev.out.log"
$ApiErr = Join-Path $Root "api\server-dev.err.log"
$WebLog = Join-Path $Root "web\server-dev.out.log"
$WebErr = Join-Path $Root "web\server-dev.err.log"

Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ApiScript) -WindowStyle Hidden -RedirectStandardOutput $ApiLog -RedirectStandardError $ApiErr
Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $WebScript) -WindowStyle Hidden -RedirectStandardOutput $WebLog -RedirectStandardError $WebErr

Start-Sleep -Seconds 4

Write-Host "Panorama Companion is starting."
Write-Host "Web: http://127.0.0.1:5173"
Write-Host "API: http://127.0.0.1:8010"
Write-Host "Logs:"
Write-Host "  $ApiLog"
Write-Host "  $ApiErr"
Write-Host "  $WebLog"
Write-Host "  $WebErr"
