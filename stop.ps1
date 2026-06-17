# ============================================================
# stop.ps1 - 停止服务
# ============================================================

Write-Host "停止服务..." -ForegroundColor Yellow

docker stop assistance-system -ErrorAction SilentlyContinue
docker rm assistance-system -ErrorAction SilentlyContinue

Write-Host "✅ 服务已停止" -ForegroundColor Green