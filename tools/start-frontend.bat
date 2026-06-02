@echo off
REM 快速启动前端服务
cd /d "%~dp0frontend"

echo 正在启动前端服务...
echo.

REM 检查依赖
if not exist "node_modules" (
    echo 安装依赖...
    call npm install
)

REM 启动服务
npm run dev

pause
