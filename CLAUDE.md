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
# 后端测试（1,597 passed: 1,385 unit + 194 integration + 18 security）
cd backend && python -m pytest tests/ -v

# 前端测试（711 passed, 1 skipped, all coverage thresholds pass）
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
cp -r frontend/dist resources/frontend

# Windows 安装包
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

**症状**: 后端正常启动，但浏览器加载页面时 JS/CSS 文件返回 404。

**常见原因**:
1. **浏览器缓存**: `index.html` 被缓存，引用的旧哈希文件已不存在 → 硬刷新 `Ctrl+Shift+R`
2. **`resources/frontend/` 与 `frontend/dist/` 不同步** → 重新 `cp -r frontend/dist resources/frontend`
