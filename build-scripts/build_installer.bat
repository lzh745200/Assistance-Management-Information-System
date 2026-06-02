@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM 创建 Windows 安装程序
REM 使用 Inno Setup 打包
REM ========================================

title 创建 Windows 安装程序

echo ========================================
echo 创建 Windows 安装程序
echo ========================================
echo.

set "PROJECT_ROOT=%~dp0"
set "VERSION=1.2.0"

REM 检查 Inno Setup 是否安装
set "INNO_SETUP="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "INNO_SETUP=C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    echo [错误] 未找到 Inno Setup
    echo.
    echo 请从以下地址下载并安装 Inno Setup:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo 或者使用便携版本:
    echo 1. 下载 Inno Setup
    echo 2. 解压到任意目录
    echo 3. 修改此脚本中的 INNO_SETUP 路径
    echo.
    pause
    exit /b 1
)

echo [OK] 找到 Inno Setup: %INNO_SETUP%
echo.

REM 检查构建产物是否存在
if not exist "dist\windows\package\backend\military-rural-backend.exe" (
    echo [错误] 未找到后端可执行文件
    echo 请先运行 build_windows_complete.bat 构建项目
    pause
    exit /b 1
)

if not exist "dist\windows\package\frontend\index.html" (
    echo [错误] 未找到前端文件
    echo 请先运行 build_windows_complete.bat 构建项目
    pause
    exit /b 1
)

echo [OK] 构建产物检查通过
echo.

REM 检查图标文件
if not exist "resources\icon.ico" (
    echo [警告] 未找到图标文件，将使用默认图标
    mkdir resources 2>nul
    REM 创建一个简单的图标占位符
    echo. > resources\icon.ico
)

REM 使用 Inno Setup 编译安装程序
echo [1/2] 编译安装程序...
echo ----------------------------------------
"%INNO_SETUP%" "installer.iss"

if errorlevel 1 (
    echo [错误] 安装程序编译失败
    pause
    exit /b 1
)

echo [OK] 安装程序编译完成
echo.

REM 检查输出文件
set "INSTALLER_FILE=dist\windows\军队乡村振兴管理系统-%VERSION%-Setup.exe"
if exist "%INSTALLER_FILE%" (
    echo [2/2] 生成文件信息...
    echo ----------------------------------------
    for %%A in ("%INSTALLER_FILE%") do (
        set "FILE_SIZE=%%~zA"
        set /a "FILE_SIZE_MB=!FILE_SIZE! / 1048576"
        echo 文件: %%~nxA
        echo 大小: !FILE_SIZE_MB! MB
        echo 路径: %%~fA
    )
    echo.
    echo ========================================
    echo 安装程序创建成功！
    echo ========================================
    echo.
    echo 安装程序位置:
    echo %INSTALLER_FILE%
    echo.
    echo 使用说明:
    echo 1. 双击运行安装程序
    echo 2. 按照向导完成安装
    echo 3. 安装完成后，从开始菜单或桌面启动系统
    echo 4. 默认访问地址: http://localhost:8000
    echo 5. 默认账户: admin / admin123
    echo.
) else (
    echo [错误] 未找到生成的安装程序
    pause
    exit /b 1
)

pause
