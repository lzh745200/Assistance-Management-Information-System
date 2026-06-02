@echo off
title 一键启动 - 军队乡村振兴管理系统

cd /d "%~dp0"

echo ╔═════════════════════════════════════════════════════════════╗
║          军队全面推进乡村振兴工作管理系统 - 一键启动            ║
╚═════════════════════════════════════════════════════════════╝
echo.

echo [1/5] 检查系统依赖...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo   ? Python 环境正常

node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)
echo   ? Node.js 环境正常

npm --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 npm，请先安装 Node.js
    pause
    exit /b 1
)
echo   ? npm 环境正常

echo.
echo [2/5] 安装后端依赖...
cd backend
pip install -q -r requirements.txt
if errorlevel 1 (
    echo 警告: 后端依赖安装可能失败，继续尝试...
)
echo   ? 后端依赖安装完成

echo.
echo [3/5] 初始化数据库...
python init_db.py
if errorlevel 1 (
    echo 警告: 数据库初始化可能失败，继续尝试...
)
echo   ? 数据库初始化完成

echo.
echo [4/5] 安装前端依赖...
cd ..\frontend
call npm install
if errorlevel 1 (
    echo 警告: 前端依赖安装可能失败，继续尝试...
)
echo   ? 前端依赖安装完成

echo.
echo [5/5] 启动服务...
echo.
echo ========================================
echo 系统启动中...
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 前端地址: http://localhost:5173
echo.
echo 按 Ctrl+C 停止所有服务
echo ========================================
echo.

start "后端服务" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
start "前端服务" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo ? 系统启动完成！
echo ========================================
echo.
echo ?? 访问地址:
echo   ? 后端 API: http://localhost:8000/api/v1
echo   ? API 文档: http://localhost:8000/docs
echo   ? 前端界面: http://localhost:5173
echo.
echo ?? 提示:
echo   ? 关闭此窗口不会停止服务
echo   ? 需要停止服务请关闭后端和前端服务窗口
echo   ? 后端日志在后端服务窗口中查看
echo   ? 前端日志在前端服务窗口中查看
echo ========================================
echo.

pause
