@echo off
title 军队乡村振兴帮扶系统启动器
color 0A

echo ========================================
echo   军队乡村振兴帮扶系统启动器
echo ========================================
echo.

REM 检查Python是否安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
echo [成功] Python环境正常
echo.

REM 检查Node.js是否安装
echo [2/4] 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)
echo [成功] Node.js环境正常
echo.

REM 安装后端依赖
echo [3/4] 检查后端依赖...
cd /d "%~dp0..\backend"
if not exist ".venv" (
    echo 正在创建Python虚拟环境...
    python -m venv .venv
)

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo 检查并安装Python依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [警告] 部分依赖安装失败，可能影响系统运行
) else (
    echo [成功] Python依赖安装完成
)
cd /d "%~dp0.."
echo.

REM 安装前端依赖
echo [4/4] 检查前端依赖...
cd /d "%~dp0..\frontend"
if not exist "node_modules" (
    echo 正在安装前端依赖，这可能需要几分钟...
    call npm install
) else (
    echo [成功] 前端依赖已存在
)
cd /d "%~dp0.."
echo.

echo ========================================
echo   系统初始化完成！
echo ========================================
echo.
echo 请选择启动方式：
echo.
echo   1. 启动后端服务
echo   2. 启动前端服务
echo   3. 同时启动前后端（推荐）
echo   4. 退出
echo.
set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_all
if "%choice%"=="4" goto end
goto invalid_choice

:start_backend
echo.
echo ========================================
echo   正在启动后端服务...
echo ========================================
echo.
cd /d "%~dp0..\backend"
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
goto end

:start_frontend
echo.
echo ========================================
echo   正在启动前端服务...
echo ========================================
echo.
cd /d "%~dp0..\frontend"
call npm run dev
goto end

:start_all
echo.
echo ========================================
echo   正在启动前后端服务...
echo ========================================
echo.
echo [后端] 启动中...
set "_BE=%~dp0..\backend"
set "_FE=%~dp0..\frontend"
start "后端服务" /d "%_BE%" cmd /k ".venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [前端] 启动中...
timeout /t 3 /nobreak >nul
start "前端服务" /d "%_FE%" cmd /k "npm run dev"

echo.
echo ========================================
echo   服务启动完成！
echo ========================================
echo.
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:5173
echo.
echo API文档: http://localhost:8000/docs
echo.
echo 系统将在浏览器中自动打开...
timeout /t 2 /nobreak >nul
start http://localhost:5173

goto end

:invalid_choice
echo.
echo [错误] 无效的选项，请重新运行脚本
pause
exit /b 1

:end
echo.
echo 按任意键退出...
pause >nul
