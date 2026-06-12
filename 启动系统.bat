@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 军队乡村振兴管理系统 - 启动中...

echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║     军队乡村振兴管理系统 v1.2.0             ║
echo   ║     一键启动                                ║
echo   ╚══════════════════════════════════════════════╝
echo.

:: ── 设置路径 ──
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: 查找 Python
set "PYTHON="
for %%p in (
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
    "python"
    "python3"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if not defined PYTHON (
        %%~p --version >nul 2>&1 && set "PYTHON=%%~p"
    )
)
if not defined PYTHON (
    echo [错误] 未找到 Python，请安装 Python 3.11+
    pause
    exit /b 1
)
echo [✓] Python: %PYTHON%

:: ── 清理旧后端进程 ──
echo [1/5] 清理后端端口...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo       端口 8000 已清理

:: ── 检查前端构建 ──
echo [2/5] 检查前端构建...
if not exist "resources\frontend\index.html" (
    echo       前端未构建，正在构建...
    cd /d "%PROJECT_ROOT%frontend"
    call npm run build >nul 2>&1
    if errorlevel 1 (
        echo       [警告] 前端构建失败，使用已有文件
    ) else (
        echo       前端构建完成
    )
    cd /d "%PROJECT_ROOT%"
    if exist "scripts\build\sync-frontend-dist.bat" (
        call scripts\build\sync-frontend-dist.bat
    )
) else (
    echo       前端已就绪
)

:: ── 初始化数据库（首次运行） ──
echo [3/5] 检查数据库...
if not exist "backend\data\rural_revitalization.db" (
    echo       首次运行，初始化数据库...
    cd /d "%PROJECT_ROOT%backend"
    %PYTHON% -c "from app.core.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine); print('数据库已初始化')"
    cd /d "%PROJECT_ROOT%"
)

:: ── 启动后端 ──
echo [4/5] 启动后端服务...
cd /d "%PROJECT_ROOT%backend"
start "军队乡村振兴系统-后端" /MIN %PYTHON% start.py
cd /d "%PROJECT_ROOT%"

:: ── 等待后端就绪 ──
echo [5/5] 等待后端就绪...
set /a count=0
:wait_backend
timeout /t 2 /nobreak >nul
netstat -ano 2>nul | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    echo       后端已就绪! (耗时约 !count! 秒)
    goto ready
)
set /a count+=2
if !count! lss 60 goto wait_backend
echo       [警告] 后端启动超时，请检查 backend\start.py

:ready
echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║  系统启动完成!                              ║
echo   ║                                            ║
echo   ║  访问地址: http://localhost:8000            ║
echo   ║  API 文档: http://localhost:8000/docs       ║
echo   ║                                            ║
echo   ║  默认账号: admin / admin123                 ║
echo   ║                                            ║
echo   ║  关闭此窗口不会停止后端服务                 ║
echo   ║  停止后端请运行: scripts\stop-all.bat       ║
echo   ╚══════════════════════════════════════════════╝
echo.

:: ── 自动打开浏览器 ──
timeout /t 3 /nobreak >nul
start http://localhost:8000

echo 按任意键关闭此窗口（不影响后端运行）...
pause >nul
