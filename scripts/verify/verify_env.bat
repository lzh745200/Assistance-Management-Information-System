@echo off
chcp 65001 >nul
echo 验证项目运行环境...
echo.

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"

echo ══════════════════════════════════════════════════════
echo   1. Python 环境检查
echo ══════════════════════════════════════════════════════
"%PYTHON_EXE%" --version
"%BACKEND_DIR%\.venv\Scripts\pip.exe" list | findstr "fastapi uvicorn sqlalchemy pydantic"
echo.

echo ══════════════════════════════════════════════════════
echo   2. Node.js 环境检查
echo ══════════════════════════════════════════════════════
node --version
npm --version
echo.

echo ══════════════════════════════════════════════════════
echo   3. 数据库检查
echo ══════════════════════════════════════════════════════
if exist "%BACKEND_DIR%\data\rural_revitalization.db" (
    echo   √ 数据库文件存在
) else (
    echo   × 数据库文件不存在（首次运行时会自动创建）
)
echo.

echo ══════════════════════════════════════════════════════
echo   4. 前端依赖检查
echo ══════════════════════════════════════════════════════
if exist "%FRONTEND_DIR%\node_modules" (
    echo   √ 前端依赖已安装
    cd /d "%FRONTEND_DIR%"
    npm list --depth=0 | findstr "vue element-plus axios"
) else (
    echo   × 前端依赖未安装
    echo   请运行: cd frontend ^&^& npm install
)
echo.

echo ══════════════════════════════════════════════════════
echo   5. 配置文件检查
echo ══════════════════════════════════════════════════════
if exist "%BACKEND_DIR%\.env" (
    echo   √ 后端配置文件存在
) else (
    echo   × 后端配置文件不存在
    echo   请复制 .env.example 为 .env
)
echo.

echo ══════════════════════════════════════════════════════
echo   环境验证完成！
echo.
echo   启动系统: 双击 "启动系统.bat"
echo ══════════════════════════════════════════════════════
echo.
pause
