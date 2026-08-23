# Start WACRM - Jalankan Backend + Buka Dashboard
Write-Host "🚀 Starting WACRM..." -ForegroundColor Green

# Cek apakah port 8000 sudah dipakai
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Backend sudah jalan di http://127.0.0.1:8000" -ForegroundColor Cyan
} catch {
    Write-Host "▶️ Starting backend..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000","--reload" -WorkingDirectory "$PSScriptRoot\backend" -WindowStyle Normal
    Start-Sleep -Seconds 4
    Write-Host "✅ Backend started" -ForegroundColor Green
}

Write-Host ""
Write-Host "📊 Dashboard: file://$PSScriptRoot\frontend\index.html" -ForegroundColor Cyan
Write-Host "🏠 Landing : file://$PSScriptRoot\landing\index.html" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Buka Dashboard dengan cara:" -ForegroundColor White
Write-Host "1. Double-klik frontend\index.html" -ForegroundColor Gray
Write-Host "   ATAU" -ForegroundColor Gray
Write-Host "2. Jalankan: npx serve frontend -p 3000" -ForegroundColor Gray
Write-Host ""

# Buka otomatis
Start-Process "http://127.0.0.1:8000/docs"
Start-Process "$PSScriptRoot\frontend\index.html"
Start-Process "$PSScriptRoot\landing\index.html"
