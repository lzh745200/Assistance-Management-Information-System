@echo off
title 数据库修复工具

echo.
echo ========================================
echo 军队乡村振兴管理系统 - 数据库修复工具
echo ========================================
echo.

set "APP_DIR=%~dp0.."
set "DB_DIR=%APP_DIR%\database"
set "DB_FILE=%DB_DIR%\military_rural.db"

echo [检查] 数据库文件状态...
echo.

if not exist "%DB_FILE%" (
    echo [提示] 数据库文件不存在
    echo 路径: %DB_FILE%
    echo.
    echo 系统将在首次启动时自动创建数据库
    pause
    exit /b 0
)

REM 显示数据库信息
for %%A in ("%DB_FILE%") do (
    echo 数据库路径: %%~fA
    echo 文件大小: %%~zA 字节
    echo 修改时间: %%~tA
)

echo.
echo 请选择操作:
echo   1. 备份当前数据库
echo   2. 删除并重新初始化数据库
echo   3. 尝试修复数据库
echo   4. 退出
echo.
set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" goto BACKUP
if "%choice%"=="2" goto REINIT
if "%choice%"=="3" goto REPAIR
goto END

:BACKUP
echo.
echo [备份] 正在备份数据库...

set "BACKUP_DIR=%DB_DIR%\backups"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_FILE=%BACKUP_DIR%\military_rural_%TIMESTAMP%.db"

copy "%DB_FILE%" "%BACKUP_FILE%" >nul 2>&1

if errorlevel 1 (
    echo [错误] 备份失败
) else (
    echo [?] 备份成功
    echo 备份文件: %BACKUP_FILE%
)

echo.
pause
goto END

:REINIT
echo.
echo [警告] 此操作将删除所有现有数据！
echo.
set /p confirm="确认要重新初始化数据库吗？(输入 YES 确认): "

if not "%confirm%"=="YES" (
    echo [取消] 操作已取消
    pause
    goto END
)

echo.
echo [备份] 先备份当前数据库...

set "BACKUP_DIR=%DB_DIR%\backups"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_FILE=%BACKUP_DIR%\military_rural_before_reinit_%TIMESTAMP%.db"

copy "%DB_FILE%" "%BACKUP_FILE%" >nul 2>&1
echo [?] 已备份到: %BACKUP_FILE%

echo.
echo [删除] 删除当前数据库...
del "%DB_FILE%" >nul 2>&1

if errorlevel 1 (
    echo [错误] 删除失败，数据库文件可能正在使用中
    echo 请先关闭系统后重试
) else (
    echo [?] 数据库已删除
    echo.
    echo [提示] 请重新启动系统，将自动创建新数据库
)

echo.
pause
goto END

:REPAIR
echo.
echo [修复] 尝试修复数据库...
echo.

REM 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，无法执行修复
    echo.
    echo 请选择其他操作或手动修复
    pause
    goto END
)

REM 创建临时修复脚本
set "REPAIR_SCRIPT=%TEMP%\db_repair.py"

echo import sqlite3 > "%REPAIR_SCRIPT%"
echo import sys >> "%REPAIR_SCRIPT%"
echo. >> "%REPAIR_SCRIPT%"
echo db_file = r'%DB_FILE%' >> "%REPAIR_SCRIPT%"
echo. >> "%REPAIR_SCRIPT%"
echo try: >> "%REPAIR_SCRIPT%"
echo     conn = sqlite3.connect(db_file) >> "%REPAIR_SCRIPT%"
echo     cursor = conn.cursor() >> "%REPAIR_SCRIPT%"
echo     cursor.execute('PRAGMA integrity_check') >> "%REPAIR_SCRIPT%"
echo     result = cursor.fetchone() >> "%REPAIR_SCRIPT%"
echo     if result[0] == 'ok': >> "%REPAIR_SCRIPT%"
echo         print('[?] 数据库完整性检查通过') >> "%REPAIR_SCRIPT%"
echo     else: >> "%REPAIR_SCRIPT%"
echo         print('[警告] 数据库存在问题:', result[0]) >> "%REPAIR_SCRIPT%"
echo         print('[尝试] 执行 VACUUM...') >> "%REPAIR_SCRIPT%"
echo         cursor.execute('VACUUM') >> "%REPAIR_SCRIPT%"
echo         print('[?] VACUUM 完成') >> "%REPAIR_SCRIPT%"
echo     conn.close() >> "%REPAIR_SCRIPT%"
echo     print('[?] 修复完成') >> "%REPAIR_SCRIPT%"
echo except Exception as e: >> "%REPAIR_SCRIPT%"
echo     print('[错误] 修复失败:', str(e)) >> "%REPAIR_SCRIPT%"
echo     sys.exit(1) >> "%REPAIR_SCRIPT%"

python "%REPAIR_SCRIPT%"

del "%REPAIR_SCRIPT%" >nul 2>&1

echo.
pause
goto END

:END
