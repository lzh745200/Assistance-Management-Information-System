@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 军队乡村振兴管理系统 - 安装包验证
echo ========================================
echo.

set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "NC=[0m"

set "PASS_COUNT=0"
set "FAIL_COUNT=0"

REM 从 package.json 读取版本号
set "PROJECT_ROOT=%~dp0..\.."
for /f %%i in ('powershell -NoProfile -Command "(Get-Content '%PROJECT_ROOT%\package.json' | ConvertFrom-Json).version"') do set "VERSION=%%i"

echo %GREEN%开始验证安装包...%NC%
echo.

:: 检查 Windows 安装包
echo [1/8] 检查 Windows .exe 安装包...
if exist "dist\electron\军队乡村振兴管理系统_%VERSION%_win_x64.exe" (
    echo %GREEN%✓ Windows 安装包存在%NC%
    for %%A in ("dist\electron\军队乡村振兴管理系统_%VERSION%_win_x64.exe") do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo   大小: !sizeMB! MB
    )
    set /a PASS_COUNT+=1
) else (
    echo %RED%✗ Windows 安装包不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查 Windows 便携版
echo [2/8] 检查 Windows 便携版...
if exist "dist\electron\军队乡村振兴管理系统_%VERSION%_Portable.exe" (
    echo %GREEN%✓ Windows 便携版存在%NC%
    for %%A in ("dist\electron\军队乡村振兴管理系统_%VERSION%_Portable.exe") do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo   大小: !sizeMB! MB
    )
    set /a PASS_COUNT+=1
) else (
    echo %RED%✗ Windows 便携版不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查 Linux DEB 包
echo [3/8] 检查 Linux .deb 安装包...
if exist "dist\installers\military-rural-system_%VERSION%_arm64.deb" (
    echo %GREEN%✓ Linux DEB 包存在%NC%
    for %%A in ("dist\installers\military-rural-system_%VERSION%_arm64.deb") do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo   大小: !sizeMB! MB
    )
    set /a PASS_COUNT+=1
) else (
    echo %RED%✗ Linux DEB 包不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查 Windows 校验和
echo [4/8] 检查 Windows 安装包校验和...
if exist "dist\electron\checksums.md5.txt" (
    if exist "dist\electron\checksums.sha256.txt" (
        echo %GREEN%✓ Windows 校验和文件存在%NC%
        set /a PASS_COUNT+=1
    ) else (
        echo %RED%✗ SHA256 校验和文件不存在%NC%
        set /a FAIL_COUNT+=1
    )
) else (
    echo %RED%✗ MD5 校验和文件不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查 Linux 校验和
echo [5/8] 检查 Linux DEB 包校验和...
if exist "dist\installers\military-rural-system_%VERSION%_arm64.deb.md5" (
    if exist "dist\installers\military-rural-system_%VERSION%_arm64.deb.sha256" (
        echo %GREEN%✓ Linux 校验和文件存在%NC%
        type "dist\installers\military-rural-system_%VERSION%_arm64.deb.md5"
        type "dist\installers\military-rural-system_%VERSION%_arm64.deb.sha256"
        set /a PASS_COUNT+=1
    ) else (
        echo %RED%✗ SHA256 校验和文件不存在%NC%
        set /a FAIL_COUNT+=1
    )
) else (
    echo %RED%✗ MD5 校验和文件不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查后端可执行文件
echo [6/8] 检查后端可执行文件...
if exist "dist\electron\win-unpacked\resources\backend\military-rural-backend.exe" (
    echo %GREEN%✓ 后端可执行文件存在%NC%
    set /a PASS_COUNT+=1
) else (
    echo %RED%✗ 后端可执行文件不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查前端文件
echo [7/8] 检查前端文件...
if exist "dist\electron\win-unpacked\resources\frontend\index.html" (
    echo %GREEN%✓ 前端文件存在%NC%
    set /a PASS_COUNT+=1
) else (
    echo %RED%✗ 前端文件不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 检查安装说明文档
echo [8/8] 检查安装说明文档...
if exist "dist\electron\安装包说明.md" (
    echo %GREEN%✓ 安装说明文档存在%NC%
    set /a PASS_COUNT+=1
) else (
    echo %YELLOW%⚠ 安装说明文档不存在%NC%
    set /a FAIL_COUNT+=1
)
echo.

:: 显示验证结果
echo ========================================
echo 验证结果汇总
echo ========================================
echo.
echo 通过检查：%GREEN%!PASS_COUNT!%NC% / 8
echo 失败检查：%RED%!FAIL_COUNT!%NC% / 8
echo.

if !FAIL_COUNT! equ 0 (
    echo %GREEN%✓ 所有检查通过，安装包验证成功！%NC%
    echo.
    echo 安装包信息：
    echo.
    echo Windows 安装包：
    echo   - NSIS 安装程序：dist\electron\军队乡村振兴管理系统_%VERSION%_win_x64.exe
    echo   - 便携版：dist\electron\军队乡村振兴管理系统_%VERSION%_Portable.exe
    echo   - 校验和：dist\electron\checksums.md5.txt / checksums.sha256.txt
    echo.
    echo Linux 安装包：
    echo   - DEB 包：dist\installers\military-rural-system_%VERSION%_arm64.deb
    echo   - 校验和：dist\installers\military-rural-system_%VERSION%_arm64.deb.md5 / .sha256
    echo.
    echo 安装方法：
    echo   Windows: 双击 .exe 文件安装
    echo   Linux: sudo dpkg -i military-rural-system_%VERSION%_arm64.deb
    echo.
) else (
    echo %YELLOW%⚠ 部分检查未通过，请检查构建过程%NC%
)

echo.
echo ========================================
pause
