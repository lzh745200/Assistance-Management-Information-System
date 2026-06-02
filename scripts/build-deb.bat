@echo off
REM ============================================================
REM 军队乡村振兴管理系统 - DEB 包构建脚本 (Windows)
REM 版本: 1.0.4
REM ============================================================

setlocal enabledelayedexpansion

set "VERSION=%~1"
set "ARCH=%~2"

if "%VERSION%"=="" set "VERSION=1.1.0"
if "%ARCH%"=="" set "ARCH=amd64"

echo.
echo ==============================================
echo   军队乡村振兴管理系统 - DEB 构建
echo ==============================================
echo.
echo   版本: %VERSION%
echo   架构: %ARCH%
echo.

REM 检查 Git Bash 是否存在
where bash >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 需要 Git Bash 环境
    echo 请使用 Git Bash 运行此脚本:
    echo   bash scripts/build-deb.sh %ARCH% %VERSION%
    exit /b 1
)

REM 使用 Git Bash 运行构建脚本
echo [INFO] 使用 Git Bash 运行构建脚本...
bash scripts/build-deb.sh %ARCH% %VERSION%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] 构建失败
    exit /b 1
)

echo.
echo ==============================================
echo   构建完成！
echo ==============================================
exit /b 0
