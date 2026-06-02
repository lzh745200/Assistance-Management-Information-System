@echo off
echo ==========================================
echo   启动军队乡村振兴管理系统（开发模式）
echo ==========================================
echo.

REM 设置项目目录
cd /d "%~dp0\.."
set PROJECT_ROOT=%CD%
echo 项目目录: %PROJECT_ROOT%
echo.

REM 检查后端Python环境
echo [1/3] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装，请先安装 Python 3.11+
    pause
    exit /b 1
)
echo   ? Python:
python --version

REM 检查前端Node.js
echo.
echo [2/3] 检查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js 未安装，请先安装 Node.js 16+
    pause
    exit /b 1
)
echo   ? Node.js:
node --version

echo.
echo ==========================================
echo [3/3] 启动服务
-echo ==========================================
echo.

REM 启动后端服务
echo 启动后端服务 (http://localhost:8000)...
cd /d "%PROJECT_ROOT%\backend"

REM 检查虚拟环境
if exist venv\Scripts\activate.bat (
    echo   使用虚拟环境
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo   使用虚拟环境
    call .venv\Scripts\activate.bat
)

start "后端服务 - 8000" cmd /k "python -m uvicorn app.main:app --reload --port 8000 --log-level info"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 检查后端是否启动成功
curl -s http://localhost:8000/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo   ? 后端启动中，请稍候...
) else (
    echo   ? 后端已就绪
)

REM 启动前端服务
echo.
echo 启动前端服务 (http://localhost:5173)...
cd /d "%PROJECT_ROOT%\frontend"

REM 检查node_modules
if not exist node_modules (
    echo   首次运行，安装依赖中...
    call npm install
    if errorlevel 1 (
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
)

start "前端服务 - 5173" cmd /k "npm run dev"

REM 等待前端启动
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo ? 服务已启动
echo ==========================================
echo.
echo 访问地址:
echo   前端: http://localhost:5173
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.
echo 401修复验证步骤:
echo   1. 打开 http://localhost:5173
echo   2. 使用管理员账号登录 (admin/admin123)
echo   3. 打开浏览器开发者工具(F12) - Network标签
echo   4. 观察API请求是否正常工作
echo   5. 保持页面10分钟以上，观察token自动刷新
echo   6. 检查控制台是否有401错误
echo.
echo 按任意键关闭此窗口（服务将继续运行）
pause >nul
