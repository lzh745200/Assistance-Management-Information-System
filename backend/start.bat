@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==================================================
echo 军队乡村振兴管理系统 - 后端服务启动脚本
echo ==================================================
echo.

:: 设置环境变量
set "BACKEND_DIR=%~dp0"
set "PYTHON=C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"

:: 检查 Python
if not exist "%PYTHON%" (
    echo [ERROR] 未找到 Python: %PYTHON%
    echo 请修改此脚本中的 PYTHON 路径为您的 Python 安装路径
    pause
    exit /b 1
)

:: 检查端口占用
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo [WARN] 端口 8000 已被占用
    echo 请关闭占用该端口的程序后重试
    pause
    exit /b 1
)

echo [OK] Python: %PYTHON%
echo [OK] 后端目录: %BACKEND_DIR%
echo.
echo 正在启动后端服务...
echo.

:: 启动服务
cd /d "%BACKEND_DIR%"
"%PYTHON%" start.py

:: 如果服务异常退出，暂停显示错误
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 服务异常退出，退出码: %errorlevel%
    pause
)
