# build-scripts — 构建脚本与配置

> Windows 离线安装包统一使用 **electron-builder**（内置 NSIS target）打包，
> 不再使用手写 .nsi 脚本。历史 7 个 .nsi 文件与 3 个 .bat 脚本已废弃删除。

## Windows 离线安装包构建

### 架构方案

```
PyInstaller (assistance-backend.spec)
  └─ backend/dist/assistance-backend.exe   (~85MB, 内含 Python + 全部依赖)
electron-builder (package.json build 段)
  ├─ extraResources: assistance-backend.exe → resources/backend/
  ├─ extraResources: frontend/dist         → resources/frontend/
  ├─ extraResources: resources/vcredist    → resources/vcredist/
  ├─ NSIS target (内置) + electron-builder-nsis-hook.nsh 钩子
  └─ dist/electron/帮扶管理系统-Setup-<version>.exe  (~250MB)
```

### 关键文件

| 文件 | 用途 |
|------|------|
| `electron-builder-nsis-hook.nsh` | electron-builder NSIS 钩子：VC++ 静默安装 + 进程终止 + 卸载数据清理 |
| `build-config.json` | 构建元数据（架构、入口、版本等） |

### 本地构建步骤

```bash
# 1. 前端构建并同步到 resources/frontend
cd frontend && npm run build
mkdir -p ../resources/frontend && cp -rf dist/* ../resources/frontend/

# 2. 后端打包（需对应架构的 Python 3.11）
cd ../backend && python -m PyInstaller assistance-backend.spec --clean --noconfirm

# 3. Electron 打包
cd ..
npx electron-builder --win --x64    # 64 位安装包
npx electron-builder --win --ia32   # 32 位安装包
```

也可使用 Makefile 快捷命令：`make build-win-x64` / `make build-win-x86` / `make build-win-all`

### 产物位置

- 安装包：`dist/electron/帮扶管理系统-Setup-<version>.exe`
- 后端 exe：`backend/dist/assistance-backend.exe`

### VC++ 运行库策略（双保险）

| 层级 | 机制 | 说明 |
|------|------|------|
| Layer 1 | PyInstaller 自动捆绑 | vcruntime140.dll / msvcp140.dll 打包进 backend.exe |
| Layer 2 | NSIS 钩子静默安装 | `vc_redist.x64.exe /install /quiet /norestart`（失败不阻断） |

目标机器无需预装任何 VC++ 运行库。

### 数据目录（非安装目录）

```
%LOCALAPPDATA%\bumofu-assistance\
├── data\rural_revitalization.db   (SQLite 数据库)
├── logs\app.log
├── uploads\
└── ...
```

数据库放在 `%LOCALAPPDATA%` 而非安装目录，避免 Program Files 权限问题。
卸载时由 NSIS 钩子询问是否删除。

## CI/CD

GitHub Actions 工作流 `.github/workflows/build-windows.yml` 自动构建 x64 + x86
双架构安装包，tag（`v*`）触发时自动发布 GitHub Release。
