@echo off
title 完整修复流程 - 登录404问题

echo.
echo ========================================
echo 军队乡村振兴管理系统
echo 登录404问题 - 完整修复流程
echo ========================================
echo.

cd /d "%~dp0.."

echo 本脚本将执行以下步骤:
echo.
echo 1. 重新构建后端（包含缺失的模块）
echo 2. 测试新构建的后端
echo 3. 更新安装包目录
echo 4. 重新构建 Electron 安装包
echo.
echo 预计耗时: 10-15 分钟
echo.

set /p confirm="是否继续？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo ========================================
echo 步骤 1/4: 重新构建后端
echo ========================================
echo.

cd backend
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 无法激活虚拟环境
    pause
    exit /b 1
)

echo 清理旧构建...
rd /s /q build dist 2>nul

echo 运行 PyInstaller（这可能需要几分钟）...
pyinstaller military-rural-backend-full.spec --clean --noconfirm

if errorlevel 1 (
    echo [错误] 后端构建失败
    pause
    exit /b 1
)

if not exist "dist\military-rural-backend.exe" (
    echo [错误] 未找到生成的可执行文件
    pause
    exit /b 1
)

echo [?] 后端构建成功
cd ..

echo.
echo ========================================
echo 步骤 2/4: 测试新构建的后端
echo ========================================
echo.

echo 复制后端到临时测试目录...
mkdir test-backend 2>nul
copy backend\dist\military-rural-backend.exe test-backend\ >nul
mkdir test-backend\database 2>nul
mkdir test-backend\logs 2>nul

echo 启动后端服务（测试模式）...
echo 按 Ctrl+C 停止测试
echo.

cd test-backend
start /B military-rural-backend.exe

echo 等待后端启动（10秒）...
timeout /t 10 >nul

echo.
echo 测试 API 端点...
echo.

echo 测试 /health:
curl -s http://localhost:8000/health
echo.

echo.
echo 测试 /api/v1/auth/login:
curl -s -X POST http://localhost:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"Admin@2026\"}"
echo.

echo.
echo 测试 /api/v1/machine-code/get-machine-code:
curl -s http://localhost:8000/api/v1/machine-code/get-machine-code
echo.

echo.
echo 关闭测试后端...
taskkill /F /IM military-rural-backend.exe >nul 2>&1

cd ..

echo.
set /p test_ok="测试是否成功？(Y/N): "
if /i not "%test_ok%"=="Y" (
    echo.
    echo 测试失败，请检查上面的输出
    echo 可以运行 scripts\启动系统-调试模式.bat 查看详细日志
    pause
    exit /b 1
)

echo.
echo ========================================
echo 步骤 3/4: 更新安装包目录
echo ========================================
echo.

echo 备份旧的后端文件...
if exist "dist\windows\package\backend\military-rural-backend.exe" (
    copy "dist\windows\package\backend\military-rural-backend.exe" ^
         "dist\windows\package\backend\military-rural-backend.exe.backup" >nul
    echo [?] 已备份旧文件
)

echo 复制新的后端文件...
copy backend\dist\military-rural-backend.exe dist\windows\package\backend\ >nul
if errorlevel 1 (
    echo [错误] 复制失败
    pause
    exit /b 1
)

echo [?] 后端文件已更新

echo.
echo ========================================
echo 步骤 4/4: 重新构建 Electron 安装包
echo ========================================
echo.

echo 运行 electron-builder（这可能需要几分钟）...
call npm run build:win-full

if errorlevel 1 (
    echo [错误] Electron 构建失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 修复完成！
echo ========================================
echo.

echo 新的安装包位于:
dir /b dist\electron\*.exe

echo.
echo 请执行以下步骤验证修复:
echo.
echo 1. 安装新的安装包到测试环境
echo 2. 运行系统并尝试登录
echo 3. 测试获取机器码功能
echo 4. 确认所有功能正常
echo.

pause
