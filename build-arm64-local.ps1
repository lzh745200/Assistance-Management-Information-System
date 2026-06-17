# 创建本地构建脚本
@'
# build-arm64-local.ps1 - 本地 ARM64 构建脚本
Write-Host "🚀 开始构建 ARM64 .deb 安装包..." -ForegroundColor Cyan

# 构建前端
if (Test-Path "frontend") {
    Write-Host "📦 构建前端..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    npm run build
    Pop-Location
}

# 设置环境变量
$env:ELECTRON_BUILDER_ARCH = "arm64"
$env:TARGET_ARCH = "arm64"

# 构建 .deb
Write-Host "📦 构建 ARM64 .deb..." -ForegroundColor Yellow
npx electron-builder --linux deb --arm64

Write-Host "✅ 构建完成" -ForegroundColor Green
Write-Host "📂 查找 .deb 文件:" -ForegroundColor Cyan
Get-ChildItem -Recurse -Filter "*.deb" | ForEach-Object {
    Write-Host "  $($_.FullName)" -ForegroundColor Yellow
    Write-Host "  大小: $([math]::Round($_.Length / 1MB, 2)) MB" -ForegroundColor Gray
}
'@ | Out-File -FilePath "build-arm64-local.ps1" -Encoding UTF8