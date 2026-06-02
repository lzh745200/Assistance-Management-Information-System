@echo off
REM 快速启动后端服务
cd /d "%~dp0backend"

echo 正在启动后端服务...
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 警告: 虚拟环境不存在，使用系统Python
)

REM 启动服务
python start.py

pause
