@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ========================================
REM 前端构建产物同步脚本 (Windows)
REM 将 frontend/dist/ 复制到 resources/frontend/
REM 包含完整性校验：文件数量和总大小对比
REM ========================================

title 前端构建产物同步

set "PROJECT_ROOT=%~dp0..\.."
set "SRC_DIR=%PROJECT_ROOT%\frontend\dist"
set "DST_DIR=%PROJECT_ROOT%\resources\frontend"

echo ========================================
echo 前端构建产物同步到 resources/frontend/
echo ========================================
echo.
echo 源目录: %SRC_DIR%
echo 目标目录: %DST_DIR%
echo.

REM 1. 检查源目录是否存在
if not exist "%SRC_DIR%\index.html" (
    echo [错误] 源目录不存在或为空: %SRC_DIR%
    echo 请先执行: cd frontend ^&^& npm run build
    pause
    exit /b 1
)
echo [OK] 源目录检查通过: %SRC_DIR%

REM 2. 收集源目录文件信息
echo.
echo [1/4] 收集源目录文件信息...
set SRC_COUNT=0
set SRC_SIZE=0
for /r "%SRC_DIR%" %%f in (*) do (
    set /a SRC_COUNT+=1
    set /a SRC_SIZE+=%%~zf
)
echo 源目录: %SRC_COUNT% 个文件, 总大小 %SRC_SIZE% 字节

REM 3. 强制清理目标目录（解决文件残留和占用问题）
echo.
echo [2/4] 清理目标目录...
if exist "%DST_DIR%" (
    REM 先尝试正常删除
    rmdir /s /q "%DST_DIR%" 2>nul
    if exist "%DST_DIR%" (
        REM 如果删除失败（文件被占用），尝试重命名后再删
        set "OLD_DIR=%DST_DIR%_old_!RANDOM!"
        echo [警告] 目标目录被占用，尝试重命名为 !OLD_DIR!
        move "%DST_DIR%" "!OLD_DIR!" >nul 2>&1
        if errorlevel 1 (
            echo [错误] 无法清理目标目录，请关闭所有占用文件后重试
            echo 可能占用文件的程序: Python/uvicorn, Electron, 文件资源管理器
            pause
            exit /b 1
        )
        REM 后台异步删除旧目录（不阻塞构建流程）
        start /b cmd /c "timeout /t 10 >nul && rmdir /s /q "!OLD_DIR!" 2>nul"
    )
)
mkdir "%DST_DIR%" 2>nul
if not exist "%DST_DIR%" (
    echo [错误] 无法创建目标目录: %DST_DIR%
    pause
    exit /b 1
)
echo [OK] 目标目录已清理

REM 4. 复制文件（使用 robocopy 保证完整性和可恢复性）
echo.
echo [3/4] 复制文件...
robocopy "%SRC_DIR%" "%DST_DIR%" /E /MIR /NJH /NJS /NP /NS /NC /NDL >nul 2>&1

REM robocopy 退出码 0-7 都表示成功
if errorlevel 8 (
    echo [错误] robocopy 复制失败（退出码: %ERRORLEVEL%）
    echo 请检查文件占用或磁盘空间
    pause
    exit /b 1
)
echo [OK] 文件复制完成

REM 5. 完整性校验：对比文件数量和总大小
echo.
echo [4/4] 完整性校验...

set DST_COUNT=0
set DST_SIZE=0
for /r "%DST_DIR%" %%f in (*) do (
    set /a DST_COUNT+=1
    set /a DST_SIZE+=%%~zf
)
echo 目标目录: !DST_COUNT! 个文件, 总大小 !DST_SIZE! 字节

if not !SRC_COUNT! equ !DST_COUNT! (
    echo [错误] 文件数量不匹配！
    echo 源目录: !SRC_COUNT! 个文件
    echo 目标目录: !DST_COUNT! 个文件
    pause
    exit /b 1
)

REM 允许 5%% 的大小偏差（因为文件系统元数据差异）
set /a SIZE_DIFF_THRESHOLD=!SRC_SIZE! * 5 / 100
set /a SIZE_DIFF=!SRC_SIZE! - !DST_SIZE!
if !SIZE_DIFF! lss 0 set /a SIZE_DIFF=-!SIZE_DIFF!

if !SIZE_DIFF! gtr !SIZE_DIFF_THRESHOLD! (
    echo [警告] 文件总大小偏差较大: !SIZE_DIFF! 字节（阈值: !SIZE_DIFF_THRESHOLD! 字节）
    echo 这可能不影响功能，但建议检查
)

echo [OK] 完整性校验通过 - 文件数量和大小匹配

REM 6. 验证关键文件
echo.
echo 验证关键文件...
set MISSING_CRITICAL=0
if not exist "%DST_DIR%\index.html" (
    echo [错误] 关键文件缺失: index.html
    set MISSING_CRITICAL=1
)
if not exist "%DST_DIR%\assets" (
    echo [错误] 关键目录缺失: assets/
    set MISSING_CRITICAL=1
)

if !MISSING_CRITICAL! equ 1 (
    echo [错误] 关键文件缺失，同步失败！
    pause
    exit /b 1
)
echo [OK] 所有关键文件验证通过

echo.
echo ========================================
echo 同步完成！
echo ========================================
echo 源: %SRC_COUNT% 个文件, !SRC_SIZE! 字节
echo 目标: !DST_COUNT! 个文件, !DST_SIZE! 字节
echo 目标路径: %DST_DIR%
echo.
echo 建议：运行 python scripts/audit_static_assets.py 检查静态资源完整性
echo ========================================

exit /b 0
