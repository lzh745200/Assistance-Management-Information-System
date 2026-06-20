# build-with-check.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  构建 ARM64 DEB 包（含配置检查）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Docker 配置
Write-Host "📋 检查 Docker 配置..." -ForegroundColor Yellow
$dockerInfo = docker info

$registryMirrors = $dockerInfo | Select-String -Pattern "Registry Mirrors"
if ($registryMirrors) {
    Write-Host "✅ Registry Mirrors 已配置:" -ForegroundColor Green
    $registryMirrors
} else {
    Write-Host "⚠️  Registry Mirrors 未配置或未生效" -ForegroundColor Yellow
    Write-Host "   请检查 Docker Desktop 设置中的 Docker Engine 配置" -ForegroundColor Yellow
    
    $continue = Read-Host "是否继续构建？(y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

# 2. 检查 BuildKit
$buildKit = $dockerInfo | Select-String -Pattern "BuildKit"
if ($buildKit) {
    Write-Host "✅ BuildKit 已启用" -ForegroundColor Green
} else {
    Write-Host "⚠️  BuildKit 未启用，将手动启用" -ForegroundColor Yellow
}

# 3. 设置构建参数
$PACKAGE_NAME = "military-rural-revitalization-system"
$PACKAGE_VERSION = "1.4.1"
$PACKAGE_ARCH = "arm64"
$OUTPUT_DIR = "./build"

# 4. 清理并创建输出目录
if (Test-Path $OUTPUT_DIR) {
    Write-Host "🧹 清理旧的构建输出..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $OUTPUT_DIR
}
New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null

# 5. 启用 BuildKit
$env:DOCKER_BUILDKIT=1

Write-Host ""
Write-Host "🚀 开始构建..." -ForegroundColor Green
Write-Host "   包名: $PACKAGE_NAME" -ForegroundColor Gray
Write-Host "   版本: $PACKAGE_VERSION" -ForegroundColor Gray
Write-Host "   架构: $PACKAGE_ARCH" -ForegroundColor Gray
Write-Host ""

# 6. 构建
$startTime = Get-Date

docker build -f Dockerfile.fpm `
    --target output `
    --platform linux/arm64 `
    --build-arg PACKAGE_NAME=$PACKAGE_NAME `
    --build-arg PACKAGE_VERSION=$PACKAGE_VERSION `
    --build-arg PACKAGE_ARCH=$PACKAGE_ARCH `
    -o $OUTPUT_DIR `
    . 2>&1 | Tee-Object -FilePath build.log

if ($LASTEXITCODE -eq 0) {
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ 构建成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📦 生成的 DEB 包：" -ForegroundColor Yellow
    Get-ChildItem $OUTPUT_DIR/*.deb | ForEach-Object {
        $size = [math]::Round($_.Length / 1MB, 2)
        Write-Host "   📄 $($_.Name) ($size MB)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "📁 输出目录: $($PWD.Path)\$OUTPUT_DIR" -ForegroundColor Yellow
    Write-Host "⏱️  构建耗时: $($duration.ToString('mm\:ss'))" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 构建日志已保存到: build.log" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ 构建失败！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "📝 查看 build.log 了解详细错误信息" -ForegroundColor Yellow
    exit 1
}