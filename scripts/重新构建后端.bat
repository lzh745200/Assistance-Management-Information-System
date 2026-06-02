@echo off
title 重新构建后端（修复404问题）

echo.
echo ========================================
echo 重新构建后端 - 修复登录404问题
echo ========================================
echo.

cd /d "%~dp0..\backend"

echo [1/3] 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 无法激活虚拟环境
    pause
    exit /b 1
)

echo [?] 虚拟环境已激活
echo.

echo [2/3] 清理旧构建...
rd /s /q build dist 2>nul
echo [?] 清理完成
echo.

echo [3/3] 运行 PyInstaller...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller military-rural-backend-full.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建完成！
echo ========================================
echo.

if exist "dist\military-rural-backend.exe" (
    echo [?] 后端可执行文件已生成
    echo 位置: backend\dist\military-rural-backend.exe

    for %%A in ("dist\military-rural-backend.exe") do (
        echo 大小: %%~zA 字节 (约 %%~zA / 1048576 MB^)
    )

    echo.
    echo 下一步:
    echo 1. 测试新构建的后端: 运行 scripts\启动系统-调试模式.bat
    echo 2. 如果测试成功，复制到安装包目录
    echo 3. 重新构建 Electron 安装包
) else (
    echo [错误] 未找到生成的可执行文件
)

echo.
pause
