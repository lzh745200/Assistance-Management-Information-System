# fix-build.ps1 - 修复构建脚本

Write-Host "========================================" -ForegroundColor Green
Write-Host "  修复安装包构建 - 一键脚本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 1. 检查前端是否已构建
if (Test-Path "frontend\dist") {
    Write-Host "✓ 前端已构建" -ForegroundColor Green
} else {
    Write-Host "✗ 前端未构建，开始构建..." -ForegroundColor Yellow
    cd frontend
    npm install
    npm run build
    cd ..
}

# 2. 创建 artifacts 目录
Write-Host "创建 artifacts 目录..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "artifacts\frontend-dist" | Out-Null

# 3. 复制前端文件
Write-Host "复制前端文件到 artifacts..." -ForegroundColor Cyan
Copy-Item -Path "frontend\dist\*" -Destination "artifacts\frontend-dist\" -Recurse -Force

# 4. 复制其他资源
if (Test-Path "resources") {
    Write-Host "复制 resources..." -ForegroundColor Cyan
    Copy-Item -Path "resources\*" -Destination "artifacts\resources\" -Recurse -Force
}

# 5. 验证
Write-Host ""
Write-Host "验证 artifacts 内容:" -ForegroundColor Cyan
Get-ChildItem -Recurse artifacts | Select-Object FullName

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 修复完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以运行你的构建命令了，例如："
Write-Host "  npm run build" -ForegroundColor Yellow
Write-Host "  或"
Write-Host "  .\build.ps1" -ForegroundColor Yellow