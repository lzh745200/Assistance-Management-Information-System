@echo off
chcp 65001 >nul
title 军队乡村振兴管理系统 - 后端服务

echo ========================================
echo   军队乡村振兴管理系统 - 后端服务
echo   版本: 1.0.3
echo ========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python版本:
python --version
echo.

:: 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [信息] 检测到虚拟环境，正在激活...
    call .venv\Scripts\activate.bat
    echo [成功] 虚拟环境已激活
    echo.
)

:: 检查依赖
echo [信息] 检查依赖包...
python -c "import fastapi, uvicorn, sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo [警告] 缺少必要的依赖包
    echo [信息] 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)
echo [成功] 依赖检查完成
echo.

:: 检查端口占用
echo [信息] 检查端口8000...
netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口8000已被占用
    echo [信息] 正在尝试终止占用进程...

    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
        echo [信息] 终止进程 PID: %%a
        taskkill /F /PID %%a >nul 2>&1
    )

    timeout /t 2 /nobreak >nul
    echo [成功] 端口已清理
)
echo.

:: 启动服务
echo [信息] 正在启动后端服务...
echo [信息] 服务地址: http://localhost:8000
echo [信息] API文档: http://localhost:8000/docs
echo [信息] 按 Ctrl+C 停止服务
echo.
echo ========================================
echo.

:: 使用安全启动脚本
python start_safe.py

:: 如果启动失败，尝试原始启动方式
if errorlevel 1 (
    echo.
    echo [警告] 安全启动失败，尝试使用原始启动方式...
    python start.py
)

:: 如果还是失败，尝试直接使用uvicorn
if errorlevel 1 (
    echo.
    echo [警告] 原始启动失败，尝试直接使用uvicorn...
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
)

echo.
echo [信息] 服务已停止
pause
