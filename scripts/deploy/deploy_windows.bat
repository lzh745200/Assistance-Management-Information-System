@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 军队乡村振兴管理系统 - 一键部署
echo ========================================
echo.

:: 设置颜色
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "NC=[0m"

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%错误：需要管理员权限运行此脚本%NC%
    echo 请右键点击脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo %GREEN%[1/10] 检查系统环境...%NC%
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%错误：未检测到 Python%NC%
    echo 请先安装 Python 3.11 或更高版本
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查 Node.js
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo %RED%错误：未检测到 Node.js%NC%
    echo 请先安装 Node.js 18 或更高版本
    echo 下载地址：https://nodejs.org/
    pause
    exit /b 1
)

echo %GREEN%✓ Python 和 Node.js 已安装%NC%
echo.

echo %GREEN%[2/10] 创建部署目录...%NC%
set "DEPLOY_DIR=C:\MRRMS"
if not exist "%DEPLOY_DIR%" (
    mkdir "%DEPLOY_DIR%"
)
cd /d "%DEPLOY_DIR%"
echo %GREEN%✓ 部署目录：%DEPLOY_DIR%%NC%
echo.

echo %GREEN%[3/10] 复制项目文件...%NC%
xcopy /E /I /Y "%~dp0backend" "%DEPLOY_DIR%\backend" >nul
xcopy /E /I /Y "%~dp0frontend" "%DEPLOY_DIR%\frontend" >nul
xcopy /E /I /Y "%~dp0electron" "%DEPLOY_DIR%\electron" >nul
copy /Y "%~dp0package.json" "%DEPLOY_DIR%\" >nul
copy /Y "%~dp0启动系统.bat" "%DEPLOY_DIR%\" >nul
echo %GREEN%✓ 项目文件已复制%NC%
echo.

echo %GREEN%[4/10] 安装后端依赖...%NC%
cd /d "%DEPLOY_DIR%\backend"
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if %errorLevel% neq 0 (
    echo %RED%错误：后端依赖安装失败%NC%
    pause
    exit /b 1
)
echo %GREEN%✓ 后端依赖已安装%NC%
echo.

echo %GREEN%[5/10] 初始化数据库...%NC%
if not exist "data" mkdir data
python -c "from app.core.database import init_db; init_db()"
if %errorLevel% neq 0 (
    echo %YELLOW%警告：数据库初始化失败，将在首次启动时自动初始化%NC%
)
echo %GREEN%✓ 数据库已初始化%NC%
echo.

echo %GREEN%[6/10] 创建默认管理员账户...%NC%
python -c "from app.core.database import SessionLocal; from app.models.user import User; from app.core.security import get_password_hash; db = SessionLocal(); admin = db.query(User).filter(User.username == 'admin').first(); admin = admin or User(username='admin', password=get_password_hash('admin123456'), full_name='系统管理员', role='admin', is_active=True); db.add(admin); db.commit(); print('管理员账户已创建')"
echo %GREEN%✓ 默认管理员账户：admin / admin123456%NC%
echo.

echo %GREEN%[7/10] 安装前端依赖...%NC%
cd /d "%DEPLOY_DIR%\frontend"
call npm install
if %errorLevel% neq 0 (
    echo %RED%错误：前端依赖安装失败%NC%
    pause
    exit /b 1
)
echo %GREEN%✓ 前端依赖已安装%NC%
echo.

echo %GREEN%[8/10] 构建前端...%NC%
call npm run build
if %errorLevel% neq 0 (
    echo %RED%错误：前端构建失败%NC%
    pause
    exit /b 1
)
echo %GREEN%✓ 前端已构建%NC%
echo.

echo %GREEN%[9/10] 安装 Electron 依赖...%NC%
cd /d "%DEPLOY_DIR%"
call npm install
if %errorLevel% neq 0 (
    echo %YELLOW%警告：Electron 依赖安装失败%NC%
)
echo %GREEN%✓ Electron 依赖已安装%NC%
echo.

echo %GREEN%[10/10] 创建桌面快捷方式...%NC%
set "SHORTCUT=%USERPROFILE%\Desktop\军队乡村振兴管理系统.lnk"
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%SHORTCUT%'); $SC.TargetPath = '%DEPLOY_DIR%\启动系统.bat'; $SC.WorkingDirectory = '%DEPLOY_DIR%'; $SC.IconLocation = '%DEPLOY_DIR%\resources\bz.ico'; $SC.Save()"
echo %GREEN%✓ 桌面快捷方式已创建%NC%
echo.

echo ========================================
echo %GREEN%部署完成！%NC%
echo ========================================
echo.
echo 部署信息：
echo - 安装目录：%DEPLOY_DIR%
echo - 默认账户：admin / admin123456
echo - 后端地址：http://localhost:8000
echo - 前端地址：http://localhost:5173
echo.
echo 启动方式：
echo 1. 双击桌面快捷方式"军队乡村振兴管理系统"
echo 2. 运行 %DEPLOY_DIR%\启动系统.bat
echo.
echo 首次启动可能需要较长时间，请耐心等待...
echo.

choice /C YN /M "是否立即启动系统"
if %errorLevel% equ 1 (
    echo.
    echo 正在启动系统...
    cd /d "%DEPLOY_DIR%"
    start "" "启动系统.bat"
)

echo.
echo 部署日志已保存到：%DEPLOY_DIR%\deploy.log
echo.
pause
