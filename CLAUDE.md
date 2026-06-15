# CLAUDE.md - 帮扶管理信息系统

## 项目概述

帮扶管理信息系统 - 完全离线的单机版桌面应用，支持多机协同数据同步。
基于 Python FastAPI 后端 + Vue 3 TypeScript 前端 + Electron 桌面壳。

> **平台说明**: 以下命令示例以 Windows 为主（`.venv\Scripts\`）。Linux/macOS 用户请将路径替换为 `.venv/bin/`、将 `\` 替换为 `/`。

> **Python 环境**: 推荐使用 Python 3.11 64-bit（`C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe`）。

## 项目结构

```
├── backend/app/              # 后端（FastAPI）
│   ├── api/v1/               # API 路由（41 个路由模块）
│   │   ├── auth/             # 认证模块
│   │   ├── data/             # 数据分析
│   │   ├── import_export/    # 异步导入导出
│   │   ├── system/           # 系统管理
│   │   └── ...               # 地图、经费、项目、帮扶村、学校、政策等
│   ├── core/                 # 核心：config, security, database, cache, data_permission
│   ├── models/               # SQLAlchemy 数据模型
│   ├── schemas/              # Pydantic 数据校验
│   ├── services/             # 业务逻辑层
│   ├── middleware/            # CSRF, 审计, 请求日志, 指标
│   └── utils/                # 工具类（含 win_proactor_fix 等平台修复）
├── backend/tests/            # 后端测试
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── security/             # 安全测试
├── backend/alembic/versions/ # Alembic 数据库迁移（Schema 权威来源）
├── frontend/src/             # 前端（Vue 3 + TypeScript）
│   ├── views/                # 页面视图
│   │   ├── dashboard/        # 工作台（QuickActions, layout editor）
│   │   ├── system/           # MonitoringDashboard 等系统页面
│   │   ├── analytics/        # 数据分析与帮扶村管理
│   │   └── ...
│   ├── components/           # 通用组件 + 业务组件
│   ├── stores/               # Pinia 状态管理
│   ├── router/               # 路由配置与守卫
│   ├── api/                  # API 请求层
│   └── utils/                # 工具函数
├── electron/                 # Electron 桌面壳
├── scripts/                  # 运维脚本
├── build-scripts/            # 构建脚本（Windows .exe / Linux ARM64 .deb）
├── docs/                     # 项目文档（01-快速开始 ~ 04-部署文档 + ER图）
└── resources/                # 图标、前端构建产物、瓦片地图
```

## 常用命令

### 开发环境启动

```bash
cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python start.py
cd frontend && npm install && npm run dev
```

### 测试

```bash
cd backend && python -m pytest tests/ -v          # 后端测试（~2300 passed）
cd frontend && npm test -- --run                  # 前端测试（~1700 passed）
cd backend && python -m flake8 app/ --max-line-length=120
cd frontend && npm run lint && npm run typecheck
```

### 构建

```bash
cd frontend && npm run build
bash scripts/build/sync-frontend-dist.sh          # 同步 + 完整性校验
python scripts/audit_static_assets.py --verbose   # 静态资源审计
build-scripts\build_windows_complete.bat          # Windows 安装包
bash build-scripts/build-linux-arm64.sh           # Linux ARM64 安装包
```

## 访问地址与默认账号

- 前端: http://localhost:5173（开发）/ http://localhost:8000（生产）
- API 文档: http://localhost:8000/docs
- 默认账号: `admin` / `admin123`

## 关键设计约定

- 项目完全离线运行，安装包内置所有运行时
- Schema 权威来源: `backend/app/models/` 和 Alembic 迁移；`database/init.sql` 已删除
- `.env` 文件不纳入版本控制
- 版本号在 `backend/app/core/config.py` → `Settings.PROJECT_VERSION`（当前 1.2.0）
- 数据库: `backend/data/rural_revitalization.db`
- 生产部署前清除测试数据: `DELETE FROM supported_villages; DELETE FROM schools;`
- **`SupportedVillage.is_revitalization_tier`** 是 Boolean（是否振兴梯队），原来的 `revitalization_tier` (String) 和 `tiered_development_level` (String) 已删除
- `TieredDevelopmentLevel` 查找表已删除
- **帮扶经费** 支持动态年度（用户可选择年份添加），不再固定 2021-2026
- **工作台自定义布局**: 支持预设布局 + 拖拽排序 + 可见性切换，状态持久化到 localStorage
- **QuickActions**: 4 组 26 个快捷入口（核心业务/数据同步/审批协作/系统管理）

## 故障排查

### 启动崩溃 - WinError 1392（文件或目录损坏）

**症状**: 后端启动时 `OSError: [WinError 1392] 文件或目录损坏且无法读取`，堆栈在 `starlette/staticfiles.py`。

**修复**: 重命名损坏目录 → 重建 → 清理。
```bash
mv resources/frontend resources/frontend_corrupted
mv frontend/node_modules frontend/node_modules_corrupted
cd frontend && npm install && npm run build && cp -r dist ../resources/frontend
```
**根本修复**: 管理员权限运行 `chkdsk D: /F` 修复文件系统。

### 前端 404 - JS/CSS Not Found

**症状**: 文件存在但浏览器 404，部分文件正常加载。

**修复**: 彻底重建 + 同步脚本 + 清除浏览器缓存。
```bash
cd frontend && npm run build
bash scripts/build/sync-frontend-dist.sh    # 先清后拷 + 校验
python scripts/audit_static_assets.py --verbose
```

### WinError 10054 - 连接重置

已在 `backend/app/utils/win_proactor_fix.py` 通过三层纵深防御修复（monkey-patch ProactorEventLoop），`start.py` 和 `main.py` 自动加载。

### 登录超时（bcrypt 5.x 兼容性）

`backend/app/core/security.py` 已注入 `_bcrypt.__about__` 使 passlib 能加载 bcrypt C 扩展，`verify_password()` 耗时从 ~30s 降至 ~200ms。
