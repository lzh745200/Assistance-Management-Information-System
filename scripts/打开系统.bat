@echo off
setlocal enabledelayedexpansion

REM ========================================
REM 军队乡村振兴管理系统 - 快速启动
REM ========================================

REM 获取版本号（从 package.json 读取）
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"version\"" package.json 2^>nul') do (
    set "VER_RAW=%%~a"
    set "VERSION=!VER_RAW:"=!"
)
if not defined VERSION (
    for /f "delims=" %%v in ('node -p "require('./package.json').version" 2^>nul') do set "VERSION=%%v"
)
if not defined VERSION set "VERSION=1.1.0"

echo.
echo 正在启动军队乡村振兴管理系统...
echo.

REM 获取脚本所在目录（向上两级到项目根目录）
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
cd /d "%PROJECT_DIR%"

REM 检查 Electron 应用是否存在
if exist "dist\win-unpacked\军队乡村振兴管理系统.exe" (
    echo [启动] Electron 应用程序...
    start "" "dist\win-unpacked\军队乡村振兴管理系统.exe"
    exit
)

REM 查找 Portable 版本
for /f "delims=" %%F in ('dir /b /o-n "dist\*Portable*.exe" 2^>nul ^| findstr /i "军队乡村振兴管理系统"') do (
    echo [提示] 请双击以下文件启动完整应用程序:
    echo.
    echo   dist\%%F
    echo.
    explorer "dist\%%F"
    exit
)

echo [错误] 未找到应用程序
echo.
echo 请确保已正确安装系统
pause
