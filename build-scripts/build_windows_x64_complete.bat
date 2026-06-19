@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ============================================
REM 帮扶管理信息系统 - Windows x64 完整构建
REM ============================================
REM 构建 64-bit 安装包，包含:
REM   1. 环境检查
REM   2. 下载 VC++ Redistributable
REM   3. 构建前端 (Vite)
REM   4. 构建后端 (PyInstaller x64)
REM   5. 组装打包目录
REM   6. NSIS 打包安装程序
REM ============================================

title 帮扶管理信息系统 - Windows x64 构建

set "PROJECT_ROOT=%~dp0.."
cd /d "%PROJECT_ROOT%"
set "VERSION=1.2.0"
set "ARCH=x64"

echo ============================================
echo   帮扶管理信息系统 v%VERSION%
echo   Windows x64 构建
echo ============================================
echo.

REM ────────────────────────────────────────
REM 1. 环境检查
REM ────────────────────────────────────────

echo [1/6] 环境检查...

where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请安装 Node.js 18+
    echo   下载: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node -v 2^>^&1') do echo   Node.js: %%i

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.11 64-bit
    echo   下载: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   Python: %%i

REM 检查 Python 是否为 64-bit
python -c "import struct; import sys; bits=struct.calcsize('P')*8; sys.exit(0 if bits==64 else 1)" 2>nul
if errorlevel 1 (
    echo [警告] 当前 Python 为 32-bit，构建的后端将为 32-bit
    echo   建议安装 64-bit Python 以获得最佳性能
)

where makensis >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
        set "NSIS=C:\Program Files (x86)\NSIS\makensis.exe"
    ) else if exist "C:\Program Files\NSIS\makensis.exe" (
        set "NSIS=C:\Program Files\NSIS\makensis.exe"
    ) else (
        echo [警告] 未找到 NSIS，将跳过安装程序打包
        echo   下载: https://nsis.sourceforge.io/Download
    )
) else (
    set "NSIS=makensis"
)

echo [OK] 环境检查通过
echo.

REM ────────────────────────────────────────
REM 2. 下载 VC++ Redistributable
REM ────────────────────────────────────────

echo [2/6] 检查 VC++ Redistributable...

if not exist "resources\vcredist" mkdir "resources\vcredist"
if not exist "resources\vcredist\vc_redist.x64.exe" (
    echo   正在下载 VC++ Redistributable (x64)...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'resources\vcredist\vc_redist.x64.exe'" 2>nul
    if errorlevel 1 (
        echo   [警告] VC++ Redistributable 下载失败，安装包将不包含运行时
        echo   手动下载: https://aka.ms/vs/17/release/vc_redist.x64.exe
        echo   下载后放置到 resources\vcredist\vc_redist.x64.exe
    ) else (
        echo   [OK] VC++ Redistributable (x64) 已下载
    )
) else (
    echo   [OK] VC++ Redistributable (x64) 已存在
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

echo   编译前端...
call npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)

if not exist "dist\index.html" (
    echo [错误] 前端构建产物不完整: dist\index.html 不存在
    pause
    exit /b 1
)

echo [OK] 前端构建完成
echo.

REM ────────────────────────────────────────
REM 4. 构建后端 (PyInstaller x64)
REM ────────────────────────────────────────

echo [4/6] 构建后端 (PyInstaller x64)...

cd /d "%PROJECT_ROOT%\backend"

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo   安装 PyInstaller...
    python -m pip install pyinstaller -q
)

if exist "assistance-management-backend.spec" (
    echo   使用 spec: assistance-management-backend.spec
    python -m PyInstaller assistance-management-backend.spec --clean --noconfirm
) else if exist "assistance-management-backend-full.spec" (
    echo   使用 spec: assistance-management-backend-full.spec
    python -m PyInstaller assistance-management-backend-full.spec --clean --noconfirm
) else (
    echo [错误] 未找到 PyInstaller spec 文件
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

REM 复制后端
if exist "dist\assistance-management-backend.exe" (
    copy "dist\assistance-management-backend.exe" "%PKG_DIR%\backend\" >nul
    echo   后端: assistance-management-backend.exe
) else (
    echo [错误] 后端构建产物不存在: dist\assistance-management-backend.exe
    pause
    exit /b 1
)

REM 复制前端
if exist "%PROJECT_ROOT%\frontend\dist" (
    xcopy "%PROJECT_ROOT%\frontend\dist" "%PKG_DIR%\frontend\" /E /I /Y /Q
    echo   前端: frontend/dist/*
) else (
    echo [错误] 前端构建产物不存在
    pause
    exit /b 1
)

echo [OK] 打包目录组装完成
echo.

REM ────────────────────────────────────────
REM 6. NSIS 打包安装程序
REM ────────────────────────────────────────

echo [6/6] NSIS 打包...

cd /d "%PROJECT_ROOT%"

if defined NSIS (
    echo   编译 NSIS 安装程序 (x64)...
    "%NSIS%" "installers\installer_x64.nsi"
    if errorlevel 1 (
        echo [警告] NSIS 编译失败，但构建产物已就绪
        echo   检查 NSIS 安装和路径设置
    ) else (
        echo   [OK] NSIS 安装程序编译完成
    )
) else (
    echo   [跳过] NSIS 未安装
    echo   安装 NSIS 后重新运行: https://nsis.sourceforge.io/Download
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
echo     安装程序:   %PROJECT_ROOT%\dist\windows\帮扶管理信息系统-%VERSION%-x64-Setup.exe
echo.
echo   手动打包 (无 NSIS):
echo     将 dist\windows\package\ 目录压缩为 zip 分发
echo     用户解压后双击 "启动系统.bat" 即可运行
echo.

pause
exit /b 0
