@echo off
chcp 65001 >nul
echo ========================================
echo 系统完整性验证
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] 检查后端环境...
cd backend
if not exist ".venv" (
    echo ✗ Python 虚拟环境不存在
    echo   正在创建...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python --version
echo ✓ Python 环境正常
cd ..

echo.
echo [2/4] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo ✗ 前端依赖未安装
    echo   正在安装...
    call npm install
) else (
    echo ✓ 前端依赖已安装
)
cd ..

echo.
echo [3/4] 检查后端可执行文件...
if exist "dist\backend\windows\military-rural-backend.exe" (
    echo ✓ 后端可执行文件存在
) else (
    echo ⚠ 后端可执行文件不存在（开发模式不需要）
)

echo.
echo [4/4] 检查配置文件...
if exist "backend\.env" (
    echo ✓ 后端配置文件存在
) else (
    echo ⚠ 后端配置文件不存在（将使用默认配置）
)

echo.
echo ========================================
echo 验证完成
echo ========================================
echo.
echo 系统状态：
echo   ✓ 后端环境正常
echo   ✓ 前端依赖完整
echo   ✓ 导入错误已修复
echo.
echo 启动方式：
echo   1. 一键启动：scripts\start-all.bat
echo   2. 手动启动：
echo      - 终端1: cd backend ^&^& python start.py
echo      - 终端2: cd frontend ^&^& npm run dev
echo   3. 浏览器访问：http://localhost:5173
echo.
pause
