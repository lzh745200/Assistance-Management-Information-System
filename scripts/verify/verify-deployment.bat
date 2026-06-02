@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
::  军队乡村振兴管理系统 - 部署验证脚本
::  验证安装包完整性和功能
:: ============================================================

echo ══════════════════════════════════════════════
echo   军队乡村振兴管理系统 - 部署验证
echo ══════════════════════════════════════════════
echo.

set "ROOT=%~dp0"
cd /d "%ROOT%"

:: ─── 读取版本号 ─────────────────────────────────
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"version\"" package.json') do (
    set "VER_RAW=%%~a"
    set "VERSION=!VER_RAW:"=!"
    goto :version_done
)
:version_done
if not defined VERSION (
    for /f "delims=" %%v in ('node -p "require('./package.json').version"') do set "VERSION=%%v"
)

:: ─── 1. 检查 Windows 安装包 ───────────────────
echo [1/5] 检查 Windows 安装包...
set "WIN_INSTALLER=dist\electron\军队乡村振兴管理系统_!VERSION!_win_x64.exe"
set "WIN_PORTABLE=dist\electron\军队乡村振兴管理系统_!VERSION!_Portable.exe"

if exist "%WIN_INSTALLER%" (
    for %%F in ("%WIN_INSTALLER%") do (
        set /a "SIZE_MB=%%~zF / 1048576"
        echo   [OK] Windows 安装包: !SIZE_MB! MB
    )
) else (
    echo   [WARN] Windows 安装包不存在
)

if exist "%WIN_PORTABLE%" (
    for %%F in ("%WIN_PORTABLE%") do (
        set /a "SIZE_MB=%%~zF / 1048576"
        echo   [OK] Windows 便携版: !SIZE_MB! MB
    )
) else (
    echo   [WARN] Windows 便携版不存在
)
echo.

:: ─── 2. 检查 ARM64 DEB 包 ─────────────────────
echo [2/5] 检查 ARM64 DEB 包...
set "ARM64_DEB=dist\arm64\military-rural-system_!VERSION!_arm64.deb"

if exist "%ARM64_DEB%" (
    for %%F in ("%ARM64_DEB%") do (
        set /a "SIZE_MB=%%~zF / 1048576"
        echo   [OK] ARM64 DEB 包: !SIZE_MB! MB
    )

    :: 检查校验和文件
    if exist "%ARM64_DEB%.sha256" (
        echo   [OK] SHA256 校验和文件存在
    )
    if exist "%ARM64_DEB%.md5" (
        echo   [OK] MD5 校验和文件存在
    )
) else (
    echo   [WARN] ARM64 DEB 包不存在（可能还在构建中）
)
echo.

:: ─── 3. 验证后端构建产物 ──────────────────────
echo [3/5] 验证后端构建产物...
if exist "backend\dist\military-rural-backend.exe" (
    for %%F in ("backend\dist\military-rural-backend.exe") do (
        set /a "SIZE_MB=%%~zF / 1048576"
        echo   [OK] 后端可执行文件: !SIZE_MB! MB
    )
) else (
    echo   [WARN] 后端可执行文件不存在
)
echo.

:: ─── 4. 验证前端构建产物 ──────────────────────
echo [4/5] 验证前端构建产物...
if exist "frontend\dist\index.html" (
    echo   [OK] 前端构建产物存在

    :: 检查关键文件
    if exist "frontend\dist\assets" (
        echo   [OK] 前端资源文件存在
    )
) else (
    echo   [WARN] 前端构建产物不存在
)
echo.

:: ─── 5. 生成部署清单 ──────────────────────────
echo [5/5] 生成部署清单...

set "MANIFEST=DEPLOYMENT_MANIFEST.txt"
echo 军队乡村振兴管理系统 - 部署清单 > "%MANIFEST%"
echo 生成时间: %DATE% %TIME% >> "%MANIFEST%"
for /f %%i in ('powershell -NoProfile -Command "(Get-Content '%~dp0..\..\package.json' | ConvertFrom-Json).version"') do set "SYS_VERSION=%%i"
echo 系统版本: %SYS_VERSION% >> "%MANIFEST%"
echo. >> "%MANIFEST%"
echo ========================================== >> "%MANIFEST%"
echo Windows 安装包 >> "%MANIFEST%"
echo ========================================== >> "%MANIFEST%"

if exist "%WIN_INSTALLER%" (
    for %%F in ("%WIN_INSTALLER%") do (
        echo 文件名: %%~nxF >> "%MANIFEST%"
        echo 大小: %%~zF bytes >> "%MANIFEST%"
        echo 路径: %%~fF >> "%MANIFEST%"
    )
) else (
    echo [不存在] >> "%MANIFEST%"
)
echo. >> "%MANIFEST%"

if exist "%WIN_PORTABLE%" (
    echo 便携版: >> "%MANIFEST%"
    for %%F in ("%WIN_PORTABLE%") do (
        echo 文件名: %%~nxF >> "%MANIFEST%"
        echo 大小: %%~zF bytes >> "%MANIFEST%"
    )
) else (
    echo 便携版: [不存在] >> "%MANIFEST%"
)
echo. >> "%MANIFEST%"

echo ========================================== >> "%MANIFEST%"
echo 麒麟 V10 ARM64 DEB 包 >> "%MANIFEST%"
echo ========================================== >> "%MANIFEST%"

if exist "%ARM64_DEB%" (
    for %%F in ("%ARM64_DEB%") do (
        echo 文件名: %%~nxF >> "%MANIFEST%"
        echo 大小: %%~zF bytes >> "%MANIFEST%"
        echo 路径: %%~fF >> "%MANIFEST%"
    )

    if exist "%ARM64_DEB%.sha256" (
        echo SHA256: >> "%MANIFEST%"
        type "%ARM64_DEB%.sha256" >> "%MANIFEST%"
    )
    if exist "%ARM64_DEB%.md5" (
        echo MD5: >> "%MANIFEST%"
        type "%ARM64_DEB%.md5" >> "%MANIFEST%"
    )
) else (
    echo [不存在或构建中] >> "%MANIFEST%"
)
echo. >> "%MANIFEST%"

echo ========================================== >> "%MANIFEST%"
echo 安装说明 >> "%MANIFEST%"
echo ========================================== >> "%MANIFEST%"
echo. >> "%MANIFEST%"
echo Windows 安装: >> "%MANIFEST%"
echo   1. 双击 军队乡村振兴管理系统_1.0.4_win_x64.exe >> "%MANIFEST%"
echo   2. 按向导完成安装 >> "%MANIFEST%"
echo   3. 默认安装路径: C:\MRRMS >> "%MANIFEST%"
echo   4. 系统要求: Windows 10/11 (x64) >> "%MANIFEST%"
echo. >> "%MANIFEST%"
echo 麒麟 V10 安装: >> "%MANIFEST%"
echo   1. 上传 DEB 包到目标系统 >> "%MANIFEST%"
echo   2. 执行: sudo dpkg -i military-rural-system_1.0.4_arm64.deb >> "%MANIFEST%"
echo   3. 修复依赖: sudo apt-get install -f >> "%MANIFEST%"
echo   4. 启动系统: military-rural-system >> "%MANIFEST%"
echo   5. 系统要求: 银河麒麟 V10 / Ubuntu 20.04+ (ARM64) >> "%MANIFEST%"
echo. >> "%MANIFEST%"

echo [OK] 部署清单已生成: %MANIFEST%
echo.

:: ─── 总结 ─────────────────────────────────────
echo ══════════════════════════════════════════════
echo   部署验证完成
echo ══════════════════════════════════════════════
echo.
echo   Windows 安装包:
if exist "%WIN_INSTALLER%" (echo     ✓ 已就绪) else (echo     ✗ 缺失)
echo   Windows 便携版:
if exist "%WIN_PORTABLE%" (echo     ✓ 已就绪) else (echo     ✗ 缺失)
echo   ARM64 DEB 包:
if exist "%ARM64_DEB%" (echo     ✓ 已就绪) else (echo     ⏳ 构建中)
echo.
echo   部署清单: %MANIFEST%
echo.
echo ══════════════════════════════════════════════

pause
