# WACRM - Stop All Services
Write-Host "🛑 Stopping WACRM..." -ForegroundColor Yellow
$ports = @(8000,3000,3001)
foreach($port in $ports){
  $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
  foreach($c in $conns){
    $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
    if($proc -and $proc.ProcessName -eq 'python'){
      Write-Host "Killing python PID $($proc.Id) on port $port" -ForegroundColor Gray
      Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
  }
}
# Fallback: kill any python http.server / uvicorn hanging
# Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "✅ Done. Ports 8000,3000,3001 freed." -ForegroundColor Green
Get-NetTCPConnection -LocalPort $ports -ErrorAction SilentlyContinue | Format-Table | Out-String | Write-Host
