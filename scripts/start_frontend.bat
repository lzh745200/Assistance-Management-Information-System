@echo off
title 前端服务 - 军队乡村振兴管理系统

echo ============================================
echo   前端服务启动
echo ============================================
echo.

cd /d "%~dp0..\frontend"

echo [检查] 依赖安装...
if not exist "node_modules" (
    echo [安装] 前端依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [启动] 前端服务 (端口: 5173)...
echo.
call npm run dev

pause
