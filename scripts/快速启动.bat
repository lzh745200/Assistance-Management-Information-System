@echo off
title 快速启动接口 - 军队乡村振兴管理系统

cd /d "%~dp0"

:menu
cls
echo ╔═══════════════════════════════════════════════════════════╗
║         军队全面推进乡村振兴工作管理系统 - 快速启动接口        ║
╚═════════════════════════════════════════════════════════════╝
echo.
echo 请选择要执行的操作：
echo.
echo   [1] 一键启动（前后端）
echo   [2] 仅启动后端
echo   [3] 仅启动前端
echo   [4] 代码质量检查
echo   [5] 代码质量检查 + 自动修复
echo   [6] 运行单元测试
echo   [7] 查看系统状态
echo   [0] 退出
echo.

set /p choice=请输入选项 [0-7]: 

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto check_quality
if "%choice%"=="5" goto fix_quality
if "%choice%"=="6" goto run_tests
if "%choice%"=="7" goto check_status
if "%choice%"=="0" goto exit
echo 无效选项，请重新选择
pause
goto menu

:start_all
echo.
echo 正在启动前后端服务...
call 一键启动.bat
goto end

:start_backend
echo.
echo 正在启动后端服务...
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
goto end

:start_frontend
echo.
echo 正在启动前端服务...
cd frontend
call npm run dev
goto end

:check_quality
echo.
echo 正在运行代码质量检查...
call 代码质量检查.bat
goto end

:fix_quality
echo.
echo 正在运行代码质量检查（自动修复模式）...
call 代码质量检查.bat --fix
goto end

:run_tests
echo.
echo 正在运行单元测试...
cd backend
python -m pytest tests/ -v
pause
goto end

:check_status
cls
echo ╔═══════════════════════════════════════════════════════════╗
║                    系统状态检查                              ║
╚═════════════════════════════════════════════════════════════╝
echo.
echo 正在检查依赖...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   ? Python 未安装
) else (
    python --version
    echo   ? Python 环境正常
)

echo.

node --version >nul 2>&1
if errorlevel 1 (
    echo   ? Node.js 未安装
) else (
    node --version
    echo   ? Node.js 环境正常
)

echo.

npm --version >nul 2>&1
if errorlevel 1 (
    echo   ? npm 未安装
) else (
    npm --version
    echo   ? npm 环境正常
)

echo.

echo 正在检查数据库...
if exist "backend\data\rural_revitalization.db" (
    echo   ? 数据库文件存在
) else (
    echo   ? 数据库文件不存在
)

echo.
echo 正在检查后端依赖...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo   ? 后端依赖未安装
) else (
    echo   ? 后端依赖已安装
)

echo.
echo 正在检查前端依赖...
if exist "frontend\node_modules" (
    echo   ? 前端依赖已安装
) else (
    echo   ? 前端依赖未安装
)

echo.
echo ========================================
echo 系统状态检查完成！
echo ========================================
echo.
pause
goto end

:exit
echo.
echo 退出
goto end

:end
