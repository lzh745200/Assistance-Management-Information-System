@echo off
REM ============================================
REM 军队乡村振兴管理系统 — 共享脚本配置
REM ============================================
REM 所有脚本通过 source 此文件获取统一的配置项，
REM 避免硬编码版本号、路径、URL 分散在各脚本中。
REM
REM 用法:
REM   call "%~dp0config.bat"
REM ============================================

REM ---- 项目路径 ----
set "PROJECT_ROOT=%~dp0.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

REM ---- 服务端口 ----
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

REM ---- URL ----
set "BACKEND_URL=http://localhost:%BACKEND_PORT%"
set "HEALTH_URL=%BACKEND_URL%/health"
set "API_DOCS_URL=%BACKEND_URL%/docs"

REM ---- 从 package.json 读取版本号 ----
set "VERSION="
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"\"version\"" "%PROJECT_ROOT%\package.json" 2^>nul') do (
    set "VER_RAW=%%a"
    set "VERSION=!VER_RAW:"=!"
    goto :config_version_done
)
:config_version_done
if not defined VERSION (
    for /f "delims=" %%v in ('node -p "require('./package.json').version" 2^>nul') do set "VERSION=%%v"
)
if not defined VERSION set "VERSION=1.1.0"

REM ---- 超时设置 ----
set "BACKEND_STARTUP_TIMEOUT=30"
