@echo off
chcp 65001 >nul
echo ========================================
echo 军队乡村振兴管理系统 - 快速修复
echo ========================================
echo.

echo [1/3] 安装 Electron 依赖...
call npm install
if errorlevel 1 (
    echo [错误] npm install 失败
    pause
    exit /b 1
)

echo.
echo [2/3] 检查后端环境...
cd backend
if not exist ".venv" (
    echo 创建 Python 虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
cd ..

echo.
echo [3/3] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)
cd ..

echo.
echo ========================================
echo ✓ 修复完成！
echo ========================================
echo.
echo 现在可以使用以下方式启动系统：
echo.
echo 方式1（推荐）: scripts\start-all.bat
echo 方式2: npm run start
echo.
pause
