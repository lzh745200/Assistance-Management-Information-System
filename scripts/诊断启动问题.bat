@echo off
setlocal enabledelayedexpansion

REM 获取版本号（从 package.json 读取）
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"version\"" package.json 2^>nul') do (
    set "VER_RAW=%%~a"
    set "VERSION=!VER_RAW:"=!"
)
if not defined VERSION (
    for /f "delims=" %%v in ('node -p "require('./package.json').version" 2^>nul') do set "VERSION=%%v"
)
if not defined VERSION set "VERSION=1.1.0"

echo ========================================
echo 军队乡村振兴管理系统 - 启动诊断
echo ========================================
echo.

REM 获取项目根目录
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

echo [诊断] 检查系统环境...
echo.

REM 1. 检查 Python 环境
echo [1] Python 环境:
python --version >nul 2>&1
if errorlevel 1 (
    python3 --version >nul 2>&1
    if errorlevel 1 (
        echo   [错误] 未找到 Python
    ) else (
        echo   [?] Python3 可用
        python3 --version
    )
) else (
    echo   [?] Python 可用
    python --version
)
echo.

REM 2. 检查后端目录
echo [2] 后端目录:
if exist "backend" (
    echo   [?] backend 目录存在
) else (
    echo   [错误] backend 目录不存在
)
echo.

REM 3. 检查虚拟环境
echo [3] Python 虚拟环境:
if exist "backend\.venv\Scripts\python.exe" (
    echo   [?] 虚拟环境存在
) else (
    echo   [警告] 虚拟环境不存在，使用系统 Python
)
echo.

REM 4. 检查打包后端
echo [4] 打包后端程序:
if exist "dist\backend\windows\military-rural-backend.exe" (
    echo   [?] 打包后端存在: dist\backend\windows\military-rural-backend.exe
) else if exist "resources\backend\military-rural-backend.exe" (
    echo   [?] 打包后端存在: resources\backend\military-rural-backend.exe
) else (
    echo   [警告] 打包后端不存在（使用开发模式）
)
echo.

REM 5. 检查前端构建
echo [5] 前端构建:
if exist "frontend\dist\index.html" (
    echo   [?] 前端构建存在: frontend\dist\index.html
) else if exist "resources\frontend\index.html" (
    echo   [?] 前端构建存在: resources\frontend\index.html
) else (
    echo   [错误] 前端构建不存在
    echo   请运行: cd frontend ^&^& npm run build
)
echo.

REM 6. 检查 Electron 应用
echo [6] Electron 应用程序:
if exist "dist\win-unpacked\军队乡村振兴管理系统.exe" (
    echo   [?] Electron 应用存在
    echo   路径: dist\win-unpacked\军队乡村振兴管理系统.exe
) else (
    echo   [警告] Electron 应用不存在
)
echo.

if exist "dist\军队乡村振兴管理系统_!VERSION!_Portable.exe" (
    echo   [?] 便携版安装包存在
    echo   路径: dist\军队乡村振兴管理系统_!VERSION!_Portable.exe
) else (
    echo   [警告] 便携版安装包不存在（请先构建）
echo.

REM 7. 检查端口占用
echo [7] 端口占用情况:
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo   [警告] 端口 8000 已被占用
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        for /f "tokens=1" %%b in ('tasklist /FI "PID eq %%a" /NH') do (
            echo   进程: %%b (PID: %%a)
        )
    )
) else (
    echo   [?] 端口 8000 可用
)
echo.

REM 8. 检查 VC++ 运行库
echo [8] Visual C++ 运行库:
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if not errorlevel 1 (
    echo   [?] VC++ 运行库已安装
) else (
    reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>&1
    if not errorlevel 1 (
        echo   [?] VC++ 运行库已安装 (WOW64)
    ) else (
        echo   [警告] 未检测到 VC++ 运行库
        echo   这可能导致后端程序无法启动
    )
)
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.

REM 提供启动建议
echo [建议的启动方式]
echo.

if exist "dist\win-unpacked\军队乡村振兴管理系统.exe" (
    echo 方式 1: 使用 Electron 应用（推荐）
    echo   双击: dist\win-unpacked\军队乡村振兴管理系统.exe
    echo.
)

if exist "backend\.venv\Scripts\python.exe" (
    echo 方式 2: 开发模式 - 使用一键启动脚本
    echo   双击: scripts\start-all.bat
    echo.
)

if exist "dist\军队乡村振兴管理系统_!VERSION!_Portable.exe" (
    echo 方式 3: 使用便携版安装包
    echo   双击: dist\军队乡村振兴管理系统_!VERSION!_Portable.exe
    echo.
)

echo.
echo 按任意键退出...
pause >nul
