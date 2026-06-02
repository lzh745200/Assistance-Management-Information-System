@echo off
echo ==========================================
echo   军队乡村振兴管理系统 - 401修复验证脚本
echo ==========================================
echo.

REM 检查目录
cd /d "%~dp0\.."
set PROJECT_ROOT=%CD%
echo 项目目录: %PROJECT_ROOT%

REM 检查Node.js
echo [1/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js 未安装，请先安装 Node.js 16+
    pause
    exit /b 1
)
echo   ? Node.js:
node --version

REM 检查Python
echo [2/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [警告] Python 未找到，跳过后端测试
    set HAS_PYTHON=0
) else (
    echo   ? Python:
    python --version
    set HAS_PYTHON=1
)

echo.
echo ==========================================
echo [3/5] 前端代码变更检查
echo ==========================================

cd /d "%PROJECT_ROOT%\frontend"

REM 检查关键文件是否存在修改
echo   检查 guards.ts 修改...
findstr /c:"ADMIN_ROLES" src\router\guards.ts >nul && (
    echo     ? ADMIN_ROLES 常量已添加
) || (
    echo     ? ADMIN_ROLES 常量未找到
)

findstr /c:"cachedAuthInfo" src\router\guards.ts >nul && (
    echo     ? 认证信息缓存已添加
) || (
    echo     ? 认证信息缓存未找到
)

findstr /c:"migrationChecked" src\router\guards.ts >nul && (
    echo     ? 迁移检查优化已添加
) || (
    echo     ? 迁移检查优化未找到
)

echo   检查 auth.ts 修改...
findstr /c:"isRefreshing" src\stores\auth.ts >nul && (
    echo     ? 全局刷新锁已添加
) || (
    echo     ? 全局刷新锁未找到
)

echo   检查 jwt.ts 存在...
if exist src\utils\jwt.ts (
    echo     ? jwt.ts 工具文件存在
) else (
    echo     ? jwt.ts 工具文件缺失
)

echo.
echo ==========================================
echo [4/5] 运行前端测试
echo ==========================================

echo   安装依赖（如有需要）...
if not exist node_modules (
    echo   首次运行，安装依赖中...
    call npm install
)

echo   运行测试套件...
call npm run test -- --run
if errorlevel 1 (
    echo [警告] 部分测试未通过，请检查
    pause
) else (
    echo   ? 所有前端测试通过
)

echo.
echo ==========================================
echo [5/5] 启动开发服务器验证
echo ==========================================

echo.
echo 准备启动开发服务器...
echo.
echo 启动后请进行以下手动验证：
echo   1. 打开 http://localhost:5173
echo   2. 使用管理员账号登录
echo   3. 观察浏览器控制台是否有401错误
echo   4. 保持页面打开10分钟以上，检查token自动刷新
echo   5. 刷新页面，确认认证状态保持
echo.

REM 询问是否启动
set /p START_SERVER="是否启动前后端开发服务器? (y/n): "
if /i "%START_SERVER%"=="y" (
    echo.
    echo 启动后端服务...
    cd /d "%PROJECT_ROOT%\backend"
    start "后端服务" cmd /k "python -m uvicorn app.main:app --reload --port 8000"

    timeout /t 3 /nobreak >nul

    echo 启动前端服务...
    cd /d "%PROJECT_ROOT%\frontend"
    start "前端服务" cmd /k "npm run dev"

    echo.
    echo ? 服务已启动
    echo   后端: http://localhost:8000
    echo   前端: http://localhost:5173
    echo.
    echo 按任意键关闭此窗口（服务将继续运行）
    pause >nul
) else (
    echo.
    echo 验证脚本完成，未启动服务器
    pause
)
