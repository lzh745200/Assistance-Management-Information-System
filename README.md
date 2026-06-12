# 军队乡村振兴管理系统

> 完全离线的单机版桌面应用 | 数据安全 | 多机协同 | 高效便捷

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![Status](https://img.shields.io/badge/status-active-success)

## 项目状态

| 指标 | 结果 |
|------|------|
| 后端测试 | 2347 passed |
| 前端测试 | 1718 passed |
| Flake8 | 0 |
| TypeScript | 0 |
| 数据库 | Alembic 迁移已应用 |

## 快速开始

### 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 64位 / 麒麟 V10 ARM64 | Windows 10/11 64位 |
| 内存 | 4 GB | 8 GB |
| 硬盘 | 2 GB 可用空间 | 5 GB 可用空间 |

> **离线设计**：安装包内置所有运行时（Python、Node.js），无需额外安装。

### 一键启动（Windows）

```bash
scripts\start-all.bat      # 启动所有服务
scripts\stop-all.bat       # 停止所有服务
```

### 手动启动

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/macOS
pip install -r requirements.txt
python start.py              # http://localhost:8000

# 前端
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

### 访问地址与默认账号

| 服务 | 地址 |
|------|------|
| 前端（开发） | http://localhost:5173 |
| 前端（生产） | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

默认账号: `admin` / `admin123`（首次登录后请修改密码）

## 技术栈

### 后端
- **框架**: FastAPI + SQLAlchemy 2.0
- **数据库**: SQLite（`backend/data/rural_revitalization.db`）
- **认证**: JWT + bcrypt + 机器码绑定
- **缓存**: diskcache（本地磁盘）+ 内存 LRU
- **打包**: PyInstaller

### 前端
- **框架**: Vue 3 + TypeScript
- **构建**: Vite
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **图表**: ECharts
- **地图**: Leaflet（离线瓦片）

### 桌面
- **壳**: Electron
- **打包**: electron-builder（Windows NSIS / Linux ARM64 DEB）

## 核心功能

| 模块 | 主要功能 |
|------|---------|
| 工作台 | 核心统计、快捷导航（26 个入口）、自定义布局、一键备份恢复 |
| 帮扶村管理 | 基础信息 CRUD、年度数据、振兴属性、帮扶经费（动态年度）、批量导入导出 |
| 帮扶学校管理 | 学校档案、学生资助、数据分析 |
| 帮扶项目管理 | 全生命周期管理、进度跟踪、里程碑 |
| 经费管理 | 资金台账、预算、审批工作流、异常检测、生命周期 |
| 乡村工作 | 任务管理、工作日志、工作日历 |
| 数据同步 | 增量导入导出、冲突解决、多机协同 |
| 数据包管理 | 版本管理、增量更新、加密传输 |
| 系统管理 | 用户/角色/菜单权限、审计日志、系统配置、健康检查 |
| 系统监控 | 监控面板（CPU/内存/磁盘/网络/进程）、API 统计、日志筛选 |

## 项目结构

```
├── backend/                  # 后端（Python + FastAPI）
│   ├── app/
│   │   ├── api/v1/          # API 路由（41 个路由模块）
│   │   ├── core/            # 核心：config, security, database, cache
│   │   ├── models/          # SQLAlchemy ORM 数据模型
│   │   ├── schemas/         # Pydantic 数据校验
│   │   ├── services/        # 业务逻辑层
│   │   ├── middleware/       # CSRF, 审计, 请求日志
│   │   └── utils/           # 工具与修复
│   ├── alembic/versions/    # 数据库迁移（Schema 权威来源）
│   └── tests/               # 测试（unit + integration + security）
├── frontend/                # 前端（Vue 3 + TypeScript）
│   └── src/
│       ├── views/           # 页面视图
│       ├── components/      # 通用组件 + 业务组件
│       ├── stores/          # Pinia 状态管理
│       ├── router/          # 路由配置与守卫
│       ├── api/             # API 请求层
│       └── utils/           # 工具函数
├── electron/                # Electron 桌面壳
├── resources/               # 图标、前端构建产物、瓦片地图
├── scripts/                 # 运维与诊断脚本
├── build-scripts/           # 构建脚本（Windows .exe / Linux .deb）
└── docs/                    # 项目文档
```

## 测试与构建

```bash
# 后端测试
cd backend && python -m pytest tests/ -v

# 前端测试
cd frontend && npm test -- --run

# 代码质量
cd backend && python -m flake8 app/ --max-line-length=120
cd frontend && npm run lint && npm run typecheck

# 构建安装包
build-scripts\build_windows_complete.bat         # Windows
bash build-scripts/build-linux-arm64.sh          # Linux ARM64
```

## 注意事项

- 项目完全离线运行，安装包内置所有运行时
- Schema 权威来源是 `backend/app/models/` 和 Alembic 迁移
- 版本号以 `backend/app/core/config.py` 中的 `Settings.PROJECT_VERSION` 为准（当前: 1.2.0）
- 数据库文件: `backend/data/rural_revitalization.db`
- 生产部署前请清除测试数据

## 文档

- [快速开始与启动指南](docs/01-快速开始/)
- [用户使用手册](docs/02-用户手册/)
- [开发文档](docs/03-开发文档/)
- [部署文档](docs/04-部署文档/)
- [ER 图与数据模型](docs/ER-DIAGRAM.md)

---

**版本**: v1.2.0 | **最后更新**: 2026-06-12
