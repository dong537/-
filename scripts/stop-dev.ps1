param(
  [int[]]$Ports = @(8010, 5173)
)

$ErrorActionPreference = "SilentlyContinue"

$pids = @()
foreach ($port in $Ports) {
  $lines = netstat -ano | Select-String ":$port\s"
  foreach ($line in $lines) {
    $parts = ($line.ToString() -split "\s+") | Where-Object { $_ }
    if ($parts.Length -ge 5 -and $parts[3] -eq "LISTENING") {
      $pids += [int]$parts[4]
    }
  }
}

$pids = $pids | Sort-Object -Unique
foreach ($processId in $pids) {
  Stop-Process -Id $processId -Force
}

if ($pids.Count -eq 0) {
  Write-Host "No Panorama Companion dev processes found on ports: $($Ports -join ', ')."
} else {
  Write-Host "Stopped Panorama Companion dev processes: $($pids -join ', ')."
}
