@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 后端实时日志监控
echo ========================================
echo.

cd /d "%~dp0backend"

:MENU
echo 选择要查看的日志:
echo   1. 应用日志 (app.log)
echo   2. 错误日志 (error.log)
echo   3. 访问日志 (access.log)
echo   4. 所有日志
echo   5. 清空日志
echo   0. 退出
echo.
set /p choice="请选择 (0-5): "

if "%choice%"=="1" goto APP_LOG
if "%choice%"=="2" goto ERROR_LOG
if "%choice%"=="3" goto ACCESS_LOG
if "%choice%"=="4" goto ALL_LOGS
if "%choice%"=="5" goto CLEAR_LOGS
if "%choice%"=="0" goto END

echo 无效选择，请重试
goto MENU

:APP_LOG
echo.
echo ========================================
echo 应用日志 (最后 50 行)
echo ========================================
powershell -Command "Get-Content logs\app.log -Tail 50 -Encoding UTF8 2>$null"
echo.
pause
goto MENU

:ERROR_LOG
echo.
echo ========================================
echo 错误日志 (最后 50 行)
echo ========================================
powershell -Command "Get-Content logs\error.log -Tail 50 -Encoding UTF8 2>$null"
echo.
pause
goto MENU

:ACCESS_LOG
echo.
echo ========================================
echo 访问日志 (最后 50 行)
echo ========================================
powershell -Command "Get-Content logs\access.log -Tail 50 -Encoding UTF8 2>$null"
echo.
pause
goto MENU

:ALL_LOGS
echo.
echo ========================================
echo 所有日志 (最后 20 行)
echo ========================================
echo.
echo [应用日志]
powershell -Command "Get-Content logs\app.log -Tail 20 -Encoding UTF8 2>$null"
echo.
echo [错误日志]
powershell -Command "Get-Content logs\error.log -Tail 20 -Encoding UTF8 2>$null"
echo.
echo [访问日志]
powershell -Command "Get-Content logs\access.log -Tail 20 -Encoding UTF8 2>$null"
echo.
pause
goto MENU

:CLEAR_LOGS
echo.
echo ========================================
echo 清空日志
echo ========================================
echo.
echo 警告: 此操作将清空所有日志文件！
set /p confirm="确认清空? (y/N): "
if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    goto MENU
)

echo. > logs\app.log
echo. > logs\error.log
echo. > logs\access.log
echo ✓ 日志已清空
pause
goto MENU

:END
echo.
echo 退出监控
endlocal
