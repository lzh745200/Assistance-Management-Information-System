@echo off
setlocal enabledelayedexpansion

REM 获取版本号（从 package.json 读取）
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"version\"" package.json 2^>nul') do (
    set "VER_RAW=%%~a"
    set "VERSION=!VER_RAW:"=!"
)
if not defined VERSION (
    for /f "delims=" %%v in ('node -p "require('./package.json').version" 2^>nul') do set "VERSION=%%v"
)
if not defined VERSION set "VERSION=1.1.0"

title 军队乡村振兴管理系统 v!VERSION! - 调试模式

echo.
echo ========================================
echo 军队乡村振兴管理系统 v!VERSION! - 调试模式
echo ========================================
echo.
echo 此模式将显示后端详细日志，用于诊断问题
echo.

REM 获取当前目录
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM 检查后端可执行文件
if not exist "backend\military-rural-backend.exe" (
    echo [错误] 未找到后端可执行文件
    pause
    exit /b 1
)

echo [启动] 启动后端服务（调试模式）...
echo.
echo ========================================
echo 后端日志输出:
echo ========================================
echo.

REM 设置环境变量
set "DATABASE_URL=sqlite:///database\military_rural.db"
set "LOG_LEVEL=DEBUG"
set "FRONTEND_DIST_PATH=%APP_DIR%frontend"

REM 直接运行后端（不使用 /B，显示输出）
"backend\military-rural-backend.exe"

echo.
echo ========================================
echo 后端服务已停止
echo ========================================
echo.
pause
