# WACRM - Start All Services (Backend + Dashboard + Landing)
Write-Host "🚀 Starting WACRM..." -ForegroundColor Green

function Test-Port($port){
  try { $c = New-Object System.Net.Sockets.TcpClient; $c.Connect("127.0.0.1",$port); $c.Close(); return $true } catch { return $false }
}
function Start-ServiceIfDown($name, $port, $workdir, $args){
  if(Test-Port $port){
    Write-Host "✅ $name already running on $port" -ForegroundColor Cyan
  } else {
    Write-Host "▶️ Starting $name on port $port..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList $args -WorkingDirectory $workdir -WindowStyle Minimized
    Start-Sleep -Seconds 3
    if(Test-Port $port){ Write-Host "✅ $name started" -ForegroundColor Green } else { Write-Host "❌ $name failed to start on $port - check $workdir" -ForegroundColor Red }
  }
}

# 1. Backend API (FastAPI + Fonnte)
Start-ServiceIfDown "Backend API" 8000 "C:\Users\owens\Documents\Saas\wacrm\backend" @("-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000")

# 2. Dashboard PWA
Start-ServiceIfDown "Dashboard" 3000 "C:\Users\owens\Documents\Saas\wacrm\frontend" @("-m","http.server","3000","--bind","0.0.0.0","--directory","C:\Users\owens\Documents\Saas\wacrm\frontend")

# 3. Landing PWA
Start-ServiceIfDown "Landing" 3001 "C:\Users\owens\Documents\Saas\wacrm\landing" @("-m","http.server","3001","--bind","0.0.0.0","--directory","C:\Users\owens\Documents\Saas\wacrm\landing")

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "✅ All services up!" -ForegroundColor Green
Write-Host "📊 Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🏠 Landing  : http://localhost:3001" -ForegroundColor Cyan
Write-Host "📚 API Docs : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "📱 HP: http://$( (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like '192.168.*'} | Select-Object -First 1).IPAddress ):3000" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

$open = Read-Host "Buka browser sekarang? (Y/n)"
if($open -ne 'n' -and $open -ne 'N'){
  Start-Process "http://localhost:3000"
  Start-Process "http://localhost:3001"
  Start-Process "http://localhost:8000/docs"
}

Write-Host "Tekan Enter untuk cek status..." -ForegroundColor Gray
Read-Host | Out-Null
Write-Host "Ports:" -ForegroundColor Gray
Get-NetTCPConnection -LocalPort 8000,3000,3001 -ErrorAction SilentlyContinue | Select-Object LocalPort, State | Format-Table | Out-String | Write-Host
Write-Host "Done. Jangan tutup window ini, minimize aja. Untuk stop: .\stop_all.ps1" -ForegroundColor Green
