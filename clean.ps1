# ============================================================
# clean.ps1 - 清理所有数据和镜像
# ============================================================

param(
    [switch]$Confirm
)

if (-not $Confirm) {
    Write-Host "警告: 此操作将删除所有数据、容器和镜像！" -ForegroundColor Red
    $response = Read-Host "确定要继续吗？[y/N]"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "操作已取消" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "停止并删除容器..." -ForegroundColor Yellow
docker stop assistance-system assistance-postgres assistance-redis -ErrorAction SilentlyContinue
docker rm assistance-system assistance-postgres assistance-redis -ErrorAction SilentlyContinue
docker network rm assistance-network -ErrorAction SilentlyContinue

Write-Host "删除镜像..." -ForegroundColor Yellow
docker rmi assistance-system:arm64 -ErrorAction SilentlyContinue

Write-Host "删除数据目录..." -ForegroundColor Yellow
Remove-Item -Recurse -Force -Path "data" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -Path "logs" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -Path "backups" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -Path "postgres-data" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force -Path "redis-data" -ErrorAction SilentlyContinue

Write-Host "删除导出的镜像文件..." -ForegroundColor Yellow
Remove-Item -Force -Path "*.tar" -ErrorAction SilentlyContinue

Write-Host "✅ 清理完成！" -ForegroundColor Green
