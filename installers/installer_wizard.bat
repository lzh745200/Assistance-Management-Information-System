@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ========================================
REM 军队乡村振兴管理系统 - 安装程序
REM 版本: 1.2.0
REM ========================================

title 军队��村振兴管理系统 - 安装向导

color 0A
cls

echo.
echo     ╔════════════════════════════════════════════════════════╗
echo     ║                                                        ║
echo     ║          军队乡村振兴管理系统 v1.2.0                  ║
echo     ║                                                        ║
echo     ║                    安装向导                            ║
echo     ║                                                        ║
echo     ╚════════════════════════════════════════════════════════╝
echo.
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此安装程序
    echo.
    echo 按任意键继续普通安装，或按 Ctrl+C 取消...
    pause >nul
)

echo [步骤 1/5] 欢迎使用安装向导
echo ════════════════════════════════════════════════════════
echo.
echo 本向导将引导您完成安装过程。
echo.
echo 按任意键继续...
pause >nul
cls

echo.
echo [步骤 2/5] 选择安装目录
echo ════════════════════════════════════════════════════════
echo.
set "DEFAULT_DIR=C:\MilitaryRuralSystem"
set "INSTALL_DIR=%DEFAULT_DIR%"

echo 默认安装目录: %DEFAULT_DIR%
echo.
set /p "CUSTOM_DIR=请输入安装目录（直接回车使用默认）: "

if not "!CUSTOM_DIR!"=="" (
    set "INSTALL_DIR=!CUSTOM_DIR!"
)

echo.
echo 将安装到: %INSTALL_DIR%
echo.
echo 按任意键继续...
pause >nul
cls

echo.
echo [步骤 3/5] 正在安装...
echo ════════════════════════════════════════════════════════
echo.

REM 创建安装目录
if not exist "%INSTALL_DIR%" (
    echo [1/4] 创建安装目录...
    mkdir "%INSTALL_DIR%" 2>nul
    if errorlevel 1 (
        echo [错误] 无法创建安装目录，请检查权限
        pause
        exit /b 1
    )
    echo [OK] 目录已创建
) else (
    echo [警告] 目录已存在，将覆盖现有文件
)

echo.
echo [2/4] 复制程序文件...
echo 这可能需要几分钟，请稍候...

REM 获取当前脚本所在目录
set "SOURCE_DIR=%~dp0"

REM 复制文件
xcopy "%SOURCE_DIR%backend" "%INSTALL_DIR%\backend\" /E /I /Y /Q >nul 2>&1
xcopy "%SOURCE_DIR%frontend" "%INSTALL_DIR%\frontend\" /E /I /Y /Q >nul 2>&1
copy "%SOURCE_DIR%启动系统.bat" "%INSTALL_DIR%\" /Y >nul 2>&1
copy "%SOURCE_DIR%安装说明.txt" "%INSTALL_DIR%\" /Y >nul 2>&1

if errorlevel 1 (
    echo [错误] 文件复制失败
    pause
    exit /b 1
)

echo [OK] 文件复制完成

echo.
echo [3/4] 创建快捷方式...

REM 创建桌面快捷方式
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\军队乡村振兴管理系统.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\启动系统.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '军队乡村振兴管理系统'; $Shortcut.Save()" >nul 2>&1

REM 创建开始菜单快捷方式
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\军队乡村振兴管理系统"
if not exist "%START_MENU%" mkdir "%START_MENU%"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\军队乡村振兴管理系统.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\启动系统.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '军队乡村振兴管理系统'; $Shortcut.Save()" >nul 2>&1

echo [OK] 快捷方式已创建

echo.
echo [4/4] 创建卸载程序...

REM 创建卸载脚本
(
echo @echo off
echo chcp 65001 ^>nul
echo title 卸载 - 军队乡村振兴管理系统
echo.
echo 确定要卸载军队乡村振兴管理系统吗？
echo.
echo 按任意键继续卸载，或关闭此窗口取消...
echo pause ^>nul
echo.
echo 正在卸载...
echo.
echo 删除程序文件...
echo rd /s /q "%INSTALL_DIR%\backend" 2^>nul
echo rd /s /q "%INSTALL_DIR%\frontend" 2^>nul
echo del /q "%INSTALL_DIR%\启动系统.bat" 2^>nul
echo del /q "%INSTALL_DIR%\安装说明.txt" 2^>nul
echo.
echo 删除快捷方式...
echo del "%USERPROFILE%\Desktop\军队乡村振兴管理系统.lnk" 2^>nul
echo rd /s /q "%START_MENU%" 2^>nul
echo.
echo 删除卸载程序...
echo del "%%~f0" 2^>nul
echo.
echo 卸载完成！
echo pause
) > "%INSTALL_DIR%\卸载.bat"

REM 创建开始菜单卸载快捷方式
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\卸载.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\卸载.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '卸载军队乡村振兴管理系统'; $Shortcut.Save()" >nul 2>&1

echo [OK] 卸载程序已创建

cls
echo.
echo [步骤 4/5] 安装完成！
echo ════════════════════════════════════════════════════════
echo.
echo ✓ 程序已成功安装到: %INSTALL_DIR%
echo ✓ 桌面快捷方式已创建
echo ✓ 开始菜单快捷方式已创建
echo.
echo 系统信息:
echo ────────────────────────────────────────────────────────
echo 访问地址: http://localhost:8000
echo 默认账户: admin
echo 默认密码: admin123
echo.
echo 按任意键继续...
pause >nul
cls

echo.
echo [步骤 5/5] 启动系统
echo ════════════════════════════════════════════════════════
echo.
set /p "START_NOW=是否立即启动系统？(Y/N): "

if /i "!START_NOW!"=="Y" (
    echo.
    echo 正在启动系统...
    start "" "%INSTALL_DIR%\启动系统.bat"
    echo.
    echo 系统已启动！
    echo 浏览器将自动打开 http://localhost:8000
) else (
    echo.
    echo 您可以通过以下方式启动系统:
    echo 1. 双击桌面快捷方式
    echo 2. 从开始菜单启动
    echo 3. 运行: %INSTALL_DIR%\启动系统.bat
)

echo.
echo.
echo 感谢使用军队乡村振兴管理系统！
echo.
pause
