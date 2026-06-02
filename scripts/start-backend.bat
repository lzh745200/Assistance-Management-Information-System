@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 后端服务启动脚本
echo ========================================
echo.

:: 检查并清理端口
echo [1/4] 检查端口占用...
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if !errorlevel! equ 0 (
    echo 端口 8000 已被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        echo   终止进程 PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo   ? 端口已清理
) else (
    echo   ? 端口 8000 可用
)

:: 切换到后端目录
echo.
echo [2/4] 切换到后端目录...
cd /d "%~dp0..\backend"
if !errorlevel! neq 0 (
    echo   ? 无法切换到后端目录
    pause
    exit /b 1
)
echo   ? 当前目录: %CD%

:: 激活虚拟环境
echo.
echo [3/4] 激活虚拟环境...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo   ? 虚拟环境已激活
) else (
    echo   ? 虚拟环境不存在，使用系统 Python
)

:: 启动服务
echo.
echo [4/4] 启动后端服务...
echo ========================================
echo 服务地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

set PYTHONIOENCODING=utf-8
python start.py

:: 如果服务异常退出
if !errorlevel! neq 0 (
    echo.
    echo ? 服务启动失败，错误码: !errorlevel!
    pause
)
