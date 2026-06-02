@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo 军队乡村振兴管理系统 - Docker 跨架构构建
echo 目标: 麒麟 V10 aarch64 DEB 安装包
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "DOCKERFILE=%PROJECT_ROOT%\Dockerfile.kylin-arm64"
set "IMAGE_NAME=military-rural-build-arm64"
set "CONTAINER_NAME=military-rural-build"

:: 检查 Docker
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Docker，请安装 Docker Desktop
    pause
    exit /b 1
)

echo [?] Docker 已找到

:: 检查 buildx
docker buildx inspect desktop-linux >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] Docker buildx 不可用
    pause
    exit /b 1
)

:: 检查 Dockerfile
if not exist "%DOCKERFILE%" (
    echo [错误] 未找到 %DOCKERFILE%
    pause
    exit /b 1
)

echo [?] 构建环境检查完成
echo.

:: 创建临时构建目录
set "TEMP_BUILD_DIR=%PROJECT_ROOT%\.build-temp"
if exist "%TEMP_BUILD_DIR%" rmdir /s /q "%TEMP_BUILD_DIR%"
mkdir "%TEMP_BUILD_DIR%"

echo [1/4] 复制项目文件...
xcopy /E /I /Y /Q "%PROJECT_ROOT%*" "%TEMP_BUILD_DIR%\"

:: 排除不需要的目录
if exist "%TEMP_BUILD_DIR%\node_modules" rmdir /s /q "%TEMP_BUILD_DIR%\node_modules"
if exist "%TEMP_BUILD_DIR%\frontend\node_modules" rmdir /s /q "%TEMP_BUILD_DIR%\frontend\node_modules"
if exist "%TEMP_BUILD_DIR%\backend\dist" rmdir /s /q "%TEMP_BUILD_DIR%\backend\dist"
if exist "%TEMP_BUILD_DIR%\backend\build" rmdir /s /q "%TEMP_BUILD_DIR%\backend\build"
if exist "%TEMP_BUILD_DIR%\frontend\dist" rmdir /s /q "%TEMP_BUILD_DIR%\frontend\dist"
if exist "%TEMP_BUILD_DIR%\dist" rmdir /s /q "%TEMP_BUILD_DIR%\dist"
if exist "%TEMP_BUILD_DIR%\.git" rmdir /s /q "%TEMP_BUILD_DIR%\.git"

echo [2/4] 构建 Docker 镜像 (aarch64)...
echo.

cd /d "%TEMP_BUILD_DIR%"
docker buildx build ^
    --platform linux/arm64 ^
    --tag %IMAGE_NAME%:latest ^
    -f "%DOCKERFILE%" ^
    --load .

if %ERRORLEVEL% neq 0 (
    echo [错误] Docker 镜像构建失败
    pause
    exit /b 1
)

echo.
echo [3/4] 在 Docker 容器中构建 DEB 包...
echo.

:: 运行构建
docker run --rm ^
    --platform=linux/arm64 ^
    --name %CONTAINER_NAME% ^
    --privileged ^
    -v "%TEMP_BUILD_DIR%:C:\build" ^
    -w C:\build ^
    %IMAGE_NAME%:latest

echo.
echo [4/4] 整理构建产物...
echo.

:: 创建输出目录
if not exist "%PROJECT_ROOT%\dist\electron" mkdir "%PROJECT_ROOT%\dist\electron"

:: 复制产物
if exist "%TEMP_BUILD_DIR%\dist\electron\*.deb" (
    copy /Y "%TEMP_BUILD_DIR%\dist\electron\*.deb" "%PROJECT_ROOT%\dist\electron\" >nul
    echo [?] DEB 包已复制
)

if exist "%TEMP_BUILD_DIR%\dist\electron\*.AppImage" (
    copy /Y "%TEMP_BUILD_DIR%\dist\electron\*.AppImage" "%PROJECT_ROOT%\dist\electron\" >nul
    echo [?] AppImage 已复制
)

:: 显示结果
echo.
echo ============================================================
echo 构建完成！
echo ============================================================
echo.

if exist "%PROJECT_ROOT%\dist\electron\*.deb" (
    echo 产物列表:
    dir /b "%PROJECT_ROOT%\dist\electron\*.deb"
    echo.
)

:: 清理临时目录
if exist "%TEMP_BUILD_DIR%" rmdir /s /q "%TEMP_BUILD_DIR%"

echo 按任意键退出...
pause >nul
