# 帮扶管理信息系统

> 完全离线的单机版桌面应用 | 多机协同数据同步 | v1.2.0

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20ARM64-orange)

## 项目状态

| 指标 | 结果 |
|------|------|
| 后端测试 | 8890+ passed, 0 skipped |
| 前端测试 | 1676+ passed |
| Flake8 | 0 错误 |
| ESLint | 0 warnings |
| vue-tsc | 0 errors |
| 测试警告 | 0 |

## 快速开始

### 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 / 麒麟 V10 ARM64 | Windows 10/11 64位 |
| 内存 | 4 GB | 8 GB |
| 硬盘 | 2 GB | 5 GB |

> **离线设计**：安装包内置所有运行时，无需安装 Python/Node.js。

### 一键启动

```bash
scripts\start-all.bat      # 启动所有服务
scripts\stop-all.bat       # 停止所有服务
```

### 开发环境

```bash
# 一键初始化开发环境
scripts\dev-setup.bat        # Windows
bash scripts/dev-setup.sh    # Linux

# 或手动
cd backend && python -m venv .venv && pip install -r requirements.txt && python start.py
cd frontend && npm install && npm run dev
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
- **框架**: FastAPI + SQLAlchemy 2.0 + Pydantic
- **数据库**: SQLite（`backend/data/rural_revitalization.db`）
- **认证**: JWT + bcrypt + 机器码绑定 + 2FA
- **缓存**: diskcache + 内存 LRU
- **任务**: APScheduler（KPI预计算/异常检测/待办提醒/周报）
- **打包**: PyInstaller（x64 + ARM64）+ electron-builder（NSIS 安装包）

### 前端
- **框架**: Vue 3 + TypeScript + Vite
- **UI**: Element Plus + ECharts + Leaflet
- **状态**: Pinia + 响应式菜单权限
- **测试**: Vitest + Playwright

### 桌面
- **壳**: Electron + electron-builder
- **安装**: NSIS (Windows) / dpkg-deb (Linux ARM64)

## 核心功能

| 模块 | 主要功能 |
|------|---------|
| 工作台 | 核心统计、快捷导航（权限控制）、自定义布局 |
| 帮扶村管理 | CRUD、10板块年度数据、批量导入导出 |
| 帮扶学校 | 学校档案、学生资助、数据分析 |
| 帮扶项目 | 全生命周期、里程碑、经费关联、Excel导入 |
| 经费管理 | 台账、预算、审批工作流、异常检测、生命周期 |
| 乡村工作 | 任务管理、工作日志、工作日历 |
| 数据同步 | 加密数据包、多机协同、冲突解决 |
| 权限管理 | RBAC角色、动态菜单、按钮级权限、数据范围隔离 |
| 系统管理 | 用户/角色/菜单、审计日志、配置、健康检查 |
| 监控面板 | CPU/内存/磁盘/网络、API统计、日志筛选 |

## 项目结构

```
├── backend/                  # 后端（Python FastAPI）
│   ├── app/api/v1/          # 47 个 API 路由模块
│   ├── app/core/            # 核心基础设施（44 模块）
│   ├── app/models/          # 60+ 数据模型（懒加载）
│   ├── app/services/        # 90+ 业务服务
│   ├── app/middleware/       # 14 个中间件
│   ├── alembic/versions/    # 数据库迁移
│   └── tests/               # 7600+ 用例
├── frontend/src/            # 前端（Vue 3 + TS）
│   ├── views/               # 32 个视图模块
│   ├── components/          # 通用 + 业务组件
│   ├── stores/              # Pinia（auth/menu/app/permission）
│   ├── router/              # 路由 + 权限守卫
│   ├── api/                 # 25+ API 模块
│   └── utils/               # 工具 + treeNormalizer
├── electron/                # Electron 桌面壳
├── resources/               # 图标、前端构建产物、瓦片
├── scripts/                 # 运维脚本 + dev-setup
├── build-scripts/           # electron-builder NSIS 钩子 + 构建配置
├── deploy/                  # 麒麟 V10 部署配置
├── docker/                  # Docker 多架构构建（ARM64 麒麟单机版）
├── .github/workflows/       # CI/CD（pr-checks + build-windows + build-arm64）
└── docs/                    # 项目文档（含系统设计 + 类图 + 时序图）
```

## 构建安装包

```bash
# 前端构建
cd frontend && npm run build

# Windows x64 安装包（PyInstaller + electron-builder）
make build-win-x64

# Windows x86 安装包（已放弃：上游科学计算包不再提供 win32 cp311 wheels）
# make build-win-x86

# Linux ARM64（Docker 交叉编译）
make build-kylin
```

产物（由 GitHub Actions 自动构建）：
- `dist/electron/帮扶管理系统 Setup 1.2.0-x64.exe` (~280 MB)
- `dist/deb/kylin/*.deb`（ARM64 麒麟 V10 单机版）

### 打包方案

PyInstaller 将 FastAPI 后端打包为 `assistance-backend.exe`（内含 Python 解释器 + 全部 pip 依赖 + SQLite），electron-builder 将其与 Electron 运行时 + Vue3 前端 + VC++ Redistributable 一起打包为 NSIS 安装包。目标机器零依赖。

## 测试

```bash
# 后端
cd backend && python -m pytest tests/ -v

# 前端
cd frontend && npm test -- --run

# 代码质量
cd backend && python -m flake8 app/ --max-line-length=120
cd frontend && npm run lint && npm run type-check
```

## 关键设计

- 项目完全离线运行，安装包内置所有运行时（Python 解释器 + 全部依赖 + SQLite + VC++ 运行库）
- 审计日志落库（audit_logs + login_attempts 表），涉军合规
- Schema 权威来源: `backend/app/models/` 和 Alembic 迁移
- 版本号: `backend/app/core/config.py` → `PROJECT_VERSION` = `1.4.1`
- 数据库: 用户目录 `%LOCALAPPDATA%/bumofu-assistance/data/rural_revitalization.db`（非安装目录）
- **菜单权限**: 后端 MENU_DEFINITIONS → `/menus/accessible` → Pinia store → 侧边栏 v-if + QuickActions v-if
- **自动备份已禁用**: 防止生成大文件占用磁盘

## 文档

- [快速开始](docs/01-快速开始/)
- [用户手册](docs/02-用户手册/)
- [开发文档](docs/03-开发文档/)
- [部署文档](docs/04-部署文档/)
- [文件结构说明](项目文件结构说明.md)
- [ER 图](docs/ER-DIAGRAM.md)

## 许可证

[MIT License](LICENSE)

---

**版本**: v1.2.0 | **更新**: 2026-07-01
