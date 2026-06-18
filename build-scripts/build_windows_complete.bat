@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ========================================
REM 帮扶管理信息系统 - Windows 完整构建
REM ========================================
REM 构建流程:
REM   1. 环境检查（Node.js, Python, VC++ 运行时）
REM   2. 构建前端 (npm run build)
REM   3. 构建后端 (PyInstaller)
REM   4. 同步前端产物到 resources/frontend/
REM   5. 静态资源完整性审计
REM   6. 打包 Windows 安装程序 (Inno Setup)
REM ========================================

title 帮扶管理信息系统 - Windows 完整构建

set "PROJECT_ROOT=%~dp0"
set "VERSION=1.3.0"

echo ========================================
echo 帮扶管理信息系统 v%VERSION%
echo Windows 完整构建
echo ========================================
echo.
echo 项目根目录: %PROJECT_ROOT%
echo.

REM ────────────────────────────────────────
REM 1. 环境检查
REM ────────────────────────────────────────

echo [1/6] 环境检查...

REM Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请安装 Node.js 18+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node -v') do echo   Node.js: %%i

REM npm
where npm >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 npm
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('npm -v') do echo   npm: %%i

REM Python
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.11+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   Python: %%i

echo [OK] 环境检查通过
echo.

REM ────────────────────────────────────────
REM 2. 构建前端
REM ────────────────────────────────────────

echo [2/6] 构建前端...

cd /d "%PROJECT_ROOT%frontend"

if not exist "node_modules\" (
    echo   安装前端依赖...
    call npm install
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
REM 3. 构建后端 (PyInstaller)
REM ────────────────────────────────────────

echo [3/6] 构建后端 (PyInstaller)...

cd /d "%PROJECT_ROOT%backend"

REM 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo   安装 PyInstaller...
    python -m pip install pyinstaller -q
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

REM 查找 spec 文件
set SPEC_FILE=
if exist "assistance-management-backend-full.spec" (
    set SPEC_FILE=assistance-management-backend-full.spec
) else if exist "assistance-management-backend.spec" (
    set SPEC_FILE=assistance-management-backend.spec
) else (
    echo [警告] 未找到 PyInstaller spec 文件，跳过后端打包
    echo   如需打包后端，请创建 .spec 文件
    goto :skip_backend
)

echo   使用 spec: !SPEC_FILE!
python -m PyInstaller !SPEC_FILE! --clean --noconfirm
if errorlevel 1 (
    echo [错误] PyInstaller 打包失败
    pause
    exit /b 1
)

echo [OK] 后端打包完成

:skip_backend
echo.

REM ────────────────────────────────────────
REM 4. 同步前端产物到 resources/frontend/
REM ────────────────────────────────────────

echo [4/6] 同步前端产物到 resources/frontend/...

if exist "%PROJECT_ROOT%scripts\build\sync-frontend-dist.bat" (
    call "%PROJECT_ROOT%scripts\build\sync-frontend-dist.bat"
    if errorlevel 1 (
        echo [错误] 前端产物同步失败
        pause
        exit /b 1
    )
) else (
    REM 备用：手动复制
    echo   使用备用复制方案...
    if exist "%PROJECT_ROOT%resources\frontend" (
        rmdir /s /q "%PROJECT_ROOT%resources\frontend" 2>nul
    )
    mkdir "%PROJECT_ROOT%resources\frontend" 2>nul
    robocopy "%PROJECT_ROOT%frontend\dist" "%PROJECT_ROOT%resources\frontend" /E /MIR /NJH /NJS /NP /NS /NC /NDL >nul 2>&1
    if errorlevel 8 (
        echo [错误] 文件复制失败
        pause
        exit /b 1
    )
)

echo [OK] 前端产物同步完成
echo.

REM ────────────────────────────────────────
REM 5. 静态资源完整性审计
REM ────────────────────────────────────────

echo [5/6] 静态资源完整性审计...

python "%PROJECT_ROOT%scripts\audit_static_assets.py" --dir "%PROJECT_ROOT%resources\frontend"
if errorlevel 2 (
    echo [错误] 审计脚本严重错误（index.html 不存在）
    pause
    exit /b 1
)
if errorlevel 1 (
    echo [错误] 静态资源完整性检查失败！存在缺失文件会导致生产环境 404
    echo 请检查前端构建日志，确保 npm run build 完整执行
    pause
    exit /b 1
)

echo [OK] 静态资源完整性审计通过
echo.

REM ────────────────────────────────────────
REM 6. 打包安装程序
REM ────────────────────────────────────────

echo [6/6] 打包安装程序...

cd /d "%PROJECT_ROOT%"

REM 检查 Inno Setup
set "INNO_SETUP="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if defined INNO_SETUP (
    if exist "installer.iss" (
        echo   使用 Inno Setup 编译安装程序...
        "%INNO_SETUP%" "installer.iss"
        if errorlevel 1 (
            echo [警告] 安装程序编译失败，但构建产物已就绪
        ) else (
            echo [OK] 安装程序生成完成
        )
    ) else (
        echo [警告] 未找到 installer.iss，跳过安装程序打包
    )
) else (
    echo [跳过] 未找到 Inno Setup，跳过安装程序打包
    echo   如需生成 .exe 安装程序，请安装 Inno Setup 6:
    echo   https://jrsoftware.org/isdl.php
)

echo.

REM ────────────────────────────────────────
REM 完成
REM ────────────────────────────────────────

echo ========================================
echo 构建完成！
echo ========================================
echo.
echo 产物位置:
echo   前端: %PROJECT_ROOT%frontend\dist\
echo   前端(部署): %PROJECT_ROOT%resources\frontend\
echo   后端: %PROJECT_ROOT%backend\dist\
echo.
echo 后续步骤:
echo   1. 启动服务: cd backend ^&^& python start.py
echo   2. 访问系统: http://127.0.0.1:8000
echo   3. 如遇 404，运行: python scripts/audit_static_assets.py
echo ========================================

pause
exit /b 0
