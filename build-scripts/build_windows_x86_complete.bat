@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ============================================
REM 帮扶管理信息系统 - Windows x86 (32-bit) 完整构建
REM ============================================
REM 构建 32-bit 安装包
REM 注意: 需要 32-bit Python 3.11
REM ============================================

title 帮扶管理信息系统 - Windows x86 构建

set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"
set "VERSION=1.2.0"
set "ARCH=x86"

echo ============================================
echo   帮扶管理信息系统 v%VERSION%
echo   Windows x86 (32-bit) 构建
echo ============================================
echo.

REM ────────────────────────────────────────
REM 1. 环境检查
REM ────────────────────────────────────────

echo [1/6] 环境检查...

where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node -v 2^>^&1') do echo   Node.js: %%i

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

REM 检查 Python 是否为 32-bit
python -c "import struct; import sys; bits=struct.calcsize('P')*8; sys.exit(0 if bits==32 else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo [错误] 当前 Python 为 64-bit，32-bit 构建需要 32-bit Python
    echo.
    echo 请按以下步骤安装 32-bit Python 3.11:
    echo   1. 下载: https://www.python.org/downloads/release/python-3119/
    echo   2. 选择 "Windows installer (32-bit)" 下载
    echo   3. 安装到 C:\Python311-32 (自定义路径，避免覆盖 64-bit)
    echo   4. 安装完成后运行:
    echo      C:\Python311-32\python.exe -m pip install pyinstaller -r backend\requirements.txt
    echo   5. 重新运行本脚本
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   Python: %%i

where makensis >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
        set "NSIS=C:\Program Files (x86)\NSIS\makensis.exe"
    ) else if exist "C:\Program Files\NSIS\makensis.exe" (
        set "NSIS=C:\Program Files\NSIS\makensis.exe"
    ) else (
        echo [警告] 未找到 NSIS
    )
) else (
    set "NSIS=makensis"
)

echo [OK] 环境检查通过
echo.

REM ────────────────────────────────────────
REM 2. 下载 VC++ Redistributable (x86)
REM ────────────────────────────────────────

echo [2/6] 检查 VC++ Redistributable (x86)...

if not exist "resources\vcredist" mkdir "resources\vcredist"
if not exist "resources\vcredist\vc_redist.x86.exe" (
    echo   正在下载 VC++ Redistributable (x86)...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x86.exe' -OutFile 'resources\vcredist\vc_redist.x86.exe'" 2>nul
    if errorlevel 1 (
        echo   [警告] 下载失败
        echo   手动下载: https://aka.ms/vs/17/release/vc_redist.x86.exe
    ) else (
        echo   [OK] VC++ Redistributable (x86) 已下载
    )
) else (
    echo   [OK] VC++ Redistributable (x86) 已存在
)
echo.

REM ────────────────────────────────────────
REM 3. 构建前端
REM ────────────────────────────────────────

echo [3/6] 构建前端...

cd /d "%PROJECT_ROOT%\frontend"

if not exist "node_modules\" (
    echo   安装前端依赖...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
)

call npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)

echo [OK] 前端构建完成
echo.

REM ────────────────────────────────────────
REM 4. 构建后端 (PyInstaller x86)
REM ────────────────────────────────────────

echo [4/6] 构建后端 (PyInstaller x86 32-bit)...

cd /d "%PROJECT_ROOT%\backend"

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo   安装 PyInstaller...
    python -m pip install pyinstaller -q
)

if exist "assistance-management-backend-x86.spec" (
    echo   使用 spec: assistance-management-backend-x86.spec
    python -m PyInstaller assistance-management-backend-x86.spec --clean --noconfirm
) else (
    echo [错误] 未找到 32-bit spec 文件: assistance-management-backend-x86.spec
    pause
    exit /b 1
)

if errorlevel 1 (
    echo [错误] PyInstaller 打包失败
    pause
    exit /b 1
)

echo [OK] 后端构建完成
echo.

REM ────────────────────────────────────────
REM 5. 组装打包目录
REM ────────────────────────────────────────

echo [5/6] 组装打包目录...

set "PKG_DIR=%PROJECT_ROOT%\dist\windows\package"
if exist "%PKG_DIR%" rmdir /s /q "%PKG_DIR%"
mkdir "%PKG_DIR%"
mkdir "%PKG_DIR%\backend"
mkdir "%PKG_DIR%\frontend"

if exist "dist\assistance-management-backend.exe" (
    copy "dist\assistance-management-backend.exe" "%PKG_DIR%\backend\" >nul
    echo   后端: assistance-management-backend.exe
)

if exist "%PROJECT_ROOT%\frontend\dist" (
    xcopy "%PROJECT_ROOT%\frontend\dist" "%PKG_DIR%\frontend\" /E /I /Y /Q
    echo   前端: frontend/dist/*
)

echo [OK] 打包目录组装完成
echo.

REM ────────────────────────────────────────
REM 6. NSIS 打包
REM ────────────────────────────────────────

echo [6/6] NSIS 打包...

cd /d "%PROJECT_ROOT%"

if defined NSIS (
    echo   编译 NSIS 安装程序 (x86)...
    "%NSIS%" "installers\installer_x86.nsi"
    if errorlevel 1 (
        echo [警告] NSIS 编译失败
    ) else (
        echo   [OK] NSIS 安装程序编译完成
    )
) else (
    echo   [跳过] NSIS 未安装
)

echo.

REM ────────────────────────────────────────
REM 完成
REM ────────────────────────────────────────

echo ============================================
echo   构建完成！
echo ============================================
echo.
echo   产物位置:
echo     后端 EXE:   %PROJECT_ROOT%\backend\dist\assistance-management-backend.exe
echo     打包目录:   %PROJECT_ROOT%\dist\windows\package\
echo     安装程序:   %PROJECT_ROOT%\dist\windows\帮扶管理信息系统-%VERSION%-x86-Setup.exe
echo.
echo   注意: 32-bit 版本不包含以下功能:
echo     - Prophet 时间序列预测
echo     - Scikit-learn 机器学习
echo     - Scipy 科学计算
echo     核心业务功能(报表、数据分析、文档生成)均正常可用
echo.

pause
exit /b 0
