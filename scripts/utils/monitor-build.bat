@echo off
REM 构建进度监控脚本

:loop
cls
echo ========================================
echo   ARM64 DEB包构建进度监控
echo ========================================
echo.
echo 任务ID: b295wi37y
echo 开始时间: %TIME%
echo.

if exist build.log (
    echo 最新构建日志 ^(最后20行^):
    echo ----------------------------------------
    powershell -Command "Get-Content build.log -Tail 20"
    echo ----------------------------------------
    echo.

    REM 检查是否完成
    findstr /C:"构建完成" build.log >nul
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [完成] 构建已完成！
        echo.
        if exist military-rural-system_*_arm64_full.deb (
            echo 生成的DEB包:
            dir /B military-rural-system_*_arm64_full.deb
            echo.
        )
        pause
        exit /b 0
    )

    REM 检查是否出错
    findstr /C:"ERROR" build.log >nul
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [错误] 构建过程中出现错误
        echo 请查看 build.log 获取详细信息
        echo.
        pause
        exit /b 1
    )
) else (
    echo 等待构建日志生成...
)

echo.
echo 按Ctrl+C停止监控，或等待30秒自动刷新...
timeout /t 30 /nobreak >nul
goto loop
