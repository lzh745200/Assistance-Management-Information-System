#!/usr/bin/env pwsh
# PowerShell 版本的全面测试脚本
# 帮扶管理信息系统 - 全面测试

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "帮扶管理信息系统 - 全面测试" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$FAILED = 0

# 后端测试
Write-Host "`n>>> 运行后端测试..." -ForegroundColor Yellow
Set-Location backend

# 创建虚拟环境（如果需要）
if (-not (Test-Path ".venv")) {
    Write-Host "创建虚拟环境..."
    python -m venv .venv
}

# 激活虚拟环境
& .venv\Scripts\Activate.ps1

# 安装依赖
pip install -e . 2>$null || pip install -r requirements.txt 2>$null

# 运行单元测试
Write-Host "运行后端单元测试..."
try {
    pytest tests/unit/ -v --tb=short --cov=app --cov-report=term-missing
    Write-Host "✓ 后端单元测试通过" -ForegroundColor Green
} catch {
    Write-Host "✗ 后端单元测试失败" -ForegroundColor Red
    $FAILED = 1
}

# 运行集成测试
Write-Host "运行后端集成测试..."
try {
    pytest tests/integration/ -v --tb=short
    Write-Host "✓ 后端集成测试通过" -ForegroundColor Green
} catch {
    Write-Host "✗ 后端集成测试失败" -ForegroundColor Red
    $FAILED = 1
}

# 检查覆盖率
Write-Host "检查后端覆盖率..."
$coverageOutput = pytest --cov=app --cov-report=term-missing 2>&1
$coverageLine = $coverageOutput | Select-String "TOTAL"
if ($coverageLine) {
    $coverage = [regex]::Match($coverageLine, '(\d+)%').Groups[1].Value
    Write-Host "后端覆盖率: $coverage%"
    if ([int]$coverage -lt 100) {
        Write-Host "✗ 后端覆盖率未达到 100%" -ForegroundColor Red
        $FAILED = 1
    } else {
        Write-Host "✓ 后端覆盖率达到 100%" -ForegroundColor Green
    }
}

Set-Location ..

# 前端测试
Write-Host "`n>>> 运行前端测试..." -ForegroundColor Yellow
Set-Location frontend

# 安装依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "安装前端依赖..."
    npm ci 2>$null
}

# 运行单元测试
Write-Host "运行前端单元测试..."
try {
    npm run test:run
    Write-Host "✓ 前端单元测试通过" -ForegroundColor Green
} catch {
    Write-Host "✗ 前端单元测试失败" -ForegroundColor Red
    $FAILED = 1
}

# 检查覆盖率
if (Test-Path "coverage/coverage-summary.json") {
    $coverageJson = Get-Content "coverage/coverage-summary.json" | ConvertFrom-Json
    $lineCoverage = $coverageJson.total.lines.pct
    Write-Host "前端行覆盖率: $lineCoverage%"
    if ($lineCoverage -lt 100) {
        Write-Host "✗ 前端覆盖率未达到 100%" -ForegroundColor Red
        $FAILED = 1
    } else {
        Write-Host "✓ 前端覆盖率达到 100%" -ForegroundColor Green
    }
}

Set-Location ..

# E2E测试（可选）
if ($env:RUN_E2E -eq "true") {
    Write-Host "`n>>> 运行 E2E 测试..." -ForegroundColor Yellow
    Set-Location frontend
    try {
        npm run test:e2e
        Write-Host "✓ E2E 测试通过" -ForegroundColor Green
    } catch {
        Write-Host "✗ E2E 测试失败" -ForegroundColor Red
        $FAILED = 1
    }
    Set-Location ..
}

# 最终结果
Write-Host "`n================================" -ForegroundColor Cyan
if ($FAILED -eq 0) {
    Write-Host "所有测试通过，可以打包部署！" -ForegroundColor Green
    exit 0
} else {
    Write-Host "测试失败，请修复后再部署！" -ForegroundColor Red
    exit 1
}
