@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM 军队乡村振兴管理系统 - Windows 原生 DEB 构建
REM 警告：需要 Linux 子系统 (WSL) 或完整 Linux 环境
REM ============================================================

echo.
echo ==============================================
echo   军队乡村振兴管理系统 - DEB 原生构建
echo ==============================================
echo.
echo [警告] 此脚本需要以下环境之一：
echo   1. WSL (Windows Subsystem for Linux)
echo   2. 完整 Linux 环境
echo   3. Git Bash with Linux 工具
echo.

REM 检查是否在 Git Bash 或 WSL 中运行
if "%OSTYPE%"=="" (
    echo [错误] 无法确定操作系统类型
    exit /b 1
)

if "%OSTYPE%"=="msys" (
    echo [检测] Git Bash 环境
) else if "%OSTYPE%"=="linux-gnu" (
    echo [检测] WSL/Linux 环境
) else (
    echo [检测] Windows 环境 - 需要 WSL
)

REM 检查必要工具
where dpkg >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] dpkg 未安装
    echo 请在 WSL 或 Linux 环境中运行
    echo.
    echo 或安装 WSL:
    echo   wsl --install
    exit /b 1
)

where pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] pyinstaller 未安装
    echo 请在 WSL/Linux 中运行:
    echo   pip install pyinstaller
    exit /b 1
)

echo [检查] 必要工具已就绪
echo.

REM 显示使用说明
echo ==============================================
echo   构建说明
echo ==============================================
echo.
echo 当前 Windows 环境无法直接构建 DEB 包，
echo DEB (Debian/Ubuntu) 包需要在 Linux 环境中构建。
echo.
echo 请选择：
echo.
echo   A) 使用 WSL/Linux 构建（推荐）
echo      在 WSL 终端中运行:
echo      bash scripts/build-deb.sh amd64
echo.
echo   B) 使用 Docker 构建（需要在有网络的环境中）
echo      确保 Docker Desktop 可以访问 Docker Hub
echo      然后运行:
echo      bash scripts/build-deb.sh amd64
echo.
echo   C) 生成 Docker 镜像用于离线传输
echo      在有网络的机器上运行 docker save
echo      然后在目标机器上运行 docker load
echo.
echo   D) 跳过构建，生成配置说明
echo.
echo ==============================================

set /p choice="请选择 (A/B/C/D): "

if /i "%choice%"=="A" (
    echo.
    echo 请在 WSL 终端中运行:
    echo   cd /mnt/c/military-Rural Revitalization-system
    echo   bash scripts/build-deb.sh amd64
    goto end
)

if /i "%choice%"=="B" (
    echo.
    echo 正在检查 Docker 网络连接...
    docker pull hello-world >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] Docker 无法连接到 Docker Hub
        echo.
        echo 请配置 Docker 镜像加速器：
        echo   打开 Docker Desktop → Settings → Docker Engine
        echo   添加以下配置后重启 Docker:
        echo   {
        echo     "registry-mirrors": [
        echo       "https://docker.mirrors.ustc.edu.cn"
        echo     ]
        echo   }
    ) else (
        echo [成功] Docker 可以连接
        echo.
        echo 运行构建:
        bash scripts/build-deb.sh amd64
    )
    goto end
)

if /i "%choice%"=="C" (
    echo.
    echo [信息] 生成离线部署指南...
    goto generate_guide
)

if /i "%choice%"=="D" (
    goto generate_guide
)

:generate_guide
echo.
echo ==============================================
echo   离线部署配置说明
echo ==============================================
echo.
echo 1. 在有网络的 Linux 服务器上：
echo    $ git clone ^<repo-url^>
echo    $ cd military-Rural-Revitalization-system
echo    $ bash scripts/build-deb.sh amd64
echo    $ ls -la dist/deb/
echo.
echo 2. 传输生成的 .deb 文件到目标机器：
echo    $ scp dist/deb/military-rural-system_1.0.4_amd64.deb ^<user^>@^<host^>:/
echo.
echo 3. 在目标机器上安装：
echo    $ sudo dpkg -i military-rural-system_1.0.4_amd64.deb
echo    $ sudo apt-get install -f  # 安装依赖
echo    $ sudo systemctl start military-rural-system
echo    $ sudo systemctl enable military-rural-system  # 开机自启
echo.
echo 4. 访问系统：
echo    浏览器打开 http://localhost:8000
echo.
echo ==============================================
echo   配置文件位置
echo ==============================================
echo.
echo 配置文件: /opt/military-rural-system/config/config.env
echo 数据目录: /opt/military-rural-system/data/
echo 日志文件: /var/log/military-rural-system/
echo 服务状态: systemctl status military-rural-system
echo.

:end
echo.
echo 按任意键退出...
pause >nul
