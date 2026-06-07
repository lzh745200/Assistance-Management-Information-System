# CLAUDE.md - 军队乡村振兴管理系统

## 项目概述

军队乡村振兴管理系统 - 完全离线的单机版桌面应用，支持多机协同数据同步。
基于 Python FastAPI 后端 + Vue 3 TypeScript 前端 + Electron 桌面壳。

> **平台说明**: 以下命令示例以 Windows 为主（`.venv\Scripts\`）。Linux/macOS 用户请将路径替换为 `.venv/bin/`、将 `\` 替换为 `/`。

> **Python 环境**: 推荐使用 Python 3.11 64-bit（`C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe`），可消除 cryptography 32-bit 性能警告。

详细技术栈和功能列表见 [README.md](README.md)。

## 项目结构

```
.
├── backend/app/              # 后端（FastAPI）
│   ├── api/v1/               # API 路由（41 个路由模块）
│   │   ├── auth/             # 认证模块
│   │   ├── data/             # 数据分析模块
│   │   ├── system/           # 系统管理模块
│   │   └── ...               # 地图、经费、项目、帮扶村等
│   ├── core/                 # 核心：config, security, database, token_manager
│   ├── models/               # SQLAlchemy 数据模型
│   ├── schemas/              # Pydantic 数据校验
│   ├── services/             # 业务逻辑层
│   ├── middleware/            # CSRF, 审计, 请求日志, 指标
│   └── utils/                # 工具类
├── backend/tests/            # 后端测试（数量见 `cd backend && pytest --collect-only -q` 实测）
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── security/             # 安全测试
├── backend/alembic/versions/ # Alembic 数据库迁移（Schema 权威来源）
├── frontend/src/             # 前端（Vue 3 + TypeScript）
│   ├── views/                # 页面视图
│   ├── components/           # 通用组件 + 业务组件
│   ├── stores/               # Pinia 状态管理
│   ├── router/               # 路由配置
│   ├── api/                  # API 请求层
│   └── utils/                # 工具函数
├── electron/                 # Electron 桌面壳
├── scripts/                  # 运维脚本
├── build-scripts/            # 构建脚本（Windows .exe / Linux ARM64 .deb）
├── docs/                     # 项目文档
├── database/init.sql         # 数据库参考 Schema（Alembic 为权威来源）
└── resources/                # 图标、前端构建产物、瓦片地图
```

## 常用命令

### 开发环境启动

```bash
# 后端（推荐使用 Python 3.11 64-bit）
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python start.py

# 前端
cd frontend
npm install
npm run dev
```

### 测试与质量检查

```bash
# 后端测试（1,598 passed: 1,385 unit + 195 integration + 18 security）
cd backend && python -m pytest tests/ -v

# 前端测试（1,664 passed, all coverage thresholds pass）
cd frontend && npm test -- --run

# 前端测试 + 覆盖率报告
cd frontend && npm test -- --run --coverage

# 代码质量
cd backend && python -m flake8 app/ --max-line-length=120
cd frontend && npm run lint && npm run typecheck
```

### 构建

```bash
# 前端构建
cd frontend && npm run build

# 同步前端产物到 resources/frontend/（含完整性校验）
# Windows
call scripts\build\sync-frontend-dist.bat
# Linux/macOS
bash scripts/build/sync-frontend-dist.sh

# 静态资源完整性审计（验证 index.html 引用的所有文件均存在）
python scripts/audit_static_assets.py [--dir resources/frontend] [--verbose]

# Windows 安装包（全部流程：构建+同步+审计+打包）
build-scripts\build_windows_complete.bat

# Linux ARM64 安装包
build-scripts\build-linux-arm64.sh
```

## 访问地址与默认账号

- 前端: http://localhost:5173（开发模式）/ http://localhost:8000（生产模式）
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 默认账号: `admin` / `admin123`（首次登录后建议修改密码）

## 注意事项

- 项目完全离线运行，安装包内置所有运行时
- Schema 权威来源是 `backend/app/models/` 和 Alembic 迁移，`database/init.sql` 仅供参考
- `.env` 文件包含敏感配置，不纳入版本控制
- 版本号以 `backend/app/core/config.py` 中的 `Settings.PROJECT_VERSION` 为准（当前: 1.2.0）
- 数据库文件位置: `backend/data/rural_revitalization.db`
- 生产部署前请清除测试数据: `DELETE FROM supported_villages; DELETE FROM schools;`

## 故障排查

### 启动崩溃 - WinError 1392（文件或目录损坏）

**症状**: 后端启动时崩溃，抛出 `OSError: [WinError 1392] 文件或目录损坏且无法读取`，
堆栈通常在 `starlette/staticfiles.py` 的 `lookup_path()` 中。

**根因**: NTFS 文件系统损坏，通常影响 `resources/frontend/assets/` 或 `frontend/node_modules/` 下的文件/目录。

**修复流程**:

```bash
# 1. 诊断 - 定位损坏文件/目录
python -c "
import os
path = '<报错路径>'
print('exists:', os.path.exists(path))
print('listdir:', os.listdir(path) if os.path.isdir(path) else 'file')
"

# 2. 绕过 - 重命名损坏目录（元数据操作，无需读取内容）
mv resources/frontend resources/frontend_corrupted
mv frontend/node_modules frontend/node_modules_corrupted

# 3. 重建
cd frontend && npm install && npm run build
cp -r frontend/dist resources/frontend

# 4. 清理（可能需要 chkdsk /F 后才能完全删除损坏目录）
cmd /c "rmdir /s /q resources\frontend_corrupted"
cmd /c "rmdir /s /q frontend\node_modules_corrupted"
```

**根本修复**: 以管理员权限运行 `chkdsk D: /F` 修复文件系统，按提示重启。

### 前端 404 - JS/CSS 文件 Not Found

**症状**: 后端正常启动，文件确实存在于磁盘，但浏览器加载页面时 JS/CSS 文件返回 404。
部分文件（如 chartjs, sortable, CSS）可能正常加载，核心业务 JS chunk 返回 404。

**根因分析**:
1. **Vite `base` 路径不匹配**: `vite.config.ts` 中 `base` 默认为 `/`（绝对路径），
   FastAPI 托管在根路径时正确，但子路径或 `file://` 协议下会断裂。
2. **构建产物 hash 不匹配**: `index.html` 引用的文件名 hash 与磁盘上的实际文件 hash 不一致，
   通常由不完整的 `frontend/dist` → `resources/frontend` 复制导致（旧文件残留 + 新文件覆盖不完整）。
3. **浏览器缓存**: 浏览器缓存的旧 `index.html` 引用已被删除的旧 hash 文件。

**修复流程**:

```bash
# 1. 彻底重建前端
cd frontend && npm run build

# 2. 使用同步脚本（自动清理旧文件 + 完整性校验）
# Windows
call scripts\build\sync-frontend-dist.bat
# Linux
bash scripts/build/sync-frontend-dist.sh

# 3. 运行审计检查
python scripts/audit_static_assets.py --verbose

# 4. 如审计通过但浏览器仍 404 → 清除浏览器缓存
# Chrome: Ctrl+Shift+Delete → "缓存的图片和文件"
# 或使用无痕模式测试

# 5. 如审计发现缺失文件：
#    - 确认 npm run build 完整执行（无错误）
#    - 确认 build 过程中没有其他程序占用 frontend/dist/
#    - 重新执行步骤 1-2
```

**预防措施**（已集成到构建流程）:
- `frontend/vite.config.ts` 显式设置 `base: '/'`，避免路径解析歧义
- `scripts/build/sync-frontend-dist.bat/.sh` — 构建同步脚本，先清后拷+校验
- `scripts/audit_static_assets.py` — 构建后审计，发现缺失立即报错阻断
- `backend/app/main.py` — `index.html` 设置 `Cache-Control: no-cache` 防止浏览器缓存
