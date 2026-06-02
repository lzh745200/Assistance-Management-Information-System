@echo off
REM 一键运行所有代码质量检测 (Windows)
REM 用法: scripts\check-all-quality.bat

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo =========================================
echo 军队乡村振兴系统 - 代码质量全面检测
echo =========================================
echo.
echo 项目路径: %PROJECT_ROOT%
echo 开始时间: %date% %time%
echo.

REM 创建总报告目录
set REPORT_DIR=%PROJECT_ROOT%\quality-reports
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set SUMMARY_FILE=%REPORT_DIR%\summary_%TIMESTAMP%.txt

echo ========================================= > "%SUMMARY_FILE%"
echo 代码质量检测汇总报告 >> "%SUMMARY_FILE%"
echo 生成时间: %date% %time% >> "%SUMMARY_FILE%"
echo ========================================= >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"

REM 后端检测
echo =========================================
echo 第一部分: 后端代码检测
echo =========================================
echo.

if exist "%SCRIPT_DIR%check-backend-quality.bat" (
    call "%SCRIPT_DIR%check-backend-quality.bat" >> "%SUMMARY_FILE%" 2>&1
) else (
    echo ??  后端检测脚本不存在
)

echo.
echo =========================================
echo 第二部分: 前端代码检测
echo =========================================
echo.

cd /d "%PROJECT_ROOT%\frontend"

if exist "scripts\check-frontend-quality.js" (
    node scripts\check-frontend-quality.js >> "%SUMMARY_FILE%" 2>&1
) else (
    echo ??  前端检测脚本不存在
)

cd /d "%PROJECT_ROOT%"

REM 生成最终汇总
echo. >> "%SUMMARY_FILE%"
echo ========================================= >> "%SUMMARY_FILE%"
echo 检测完成 >> "%SUMMARY_FILE%"
echo ========================================= >> "%SUMMARY_FILE%"
echo 结束时间: %date% %time% >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"

echo.
echo =========================================
echo 全部检测完成！
echo =========================================
echo.
echo ?? 汇总报告: %SUMMARY_FILE%
echo ?? 详细报告: %REPORT_DIR%\
echo.
echo ?? 下一步建议:
echo   1. 查看汇总报告了解整体质量状况
echo   2. 优先修复高危安全漏洞
echo   3. 逐步提升代码质量评分
echo   4. 定期运行此脚本监控代码质量
echo.

pause
