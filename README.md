# 军队乡村振兴管理系统

> 完全离线的单机版桌面应用 | 数据安全 | 多机协同 | 高效便捷

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![Status](https://img.shields.io/badge/status-active-success)

## 项目状态

- 后端测试：全部通过
- 前端测试：全部通过
- Flake8：0 错误
- TypeScript：0 错误
- ESLint：0 错误
- 数据库：Alembic 迁移已应用

## 快速开始

### 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 64位 | Windows 10/11 64位 |
| 内存 | 4 GB | 8 GB |
| 硬盘 | 2 GB 可用空间 | 5 GB 可用空间 |

> **离线设计**：安装包内置所有运行时（Python、Node.js），无需额外安装。

### 一键启动（Windows）

```bash
# 启动所有服务（自动清理端口冲突）
scripts\start-all.bat

# 停止所有服务
scripts\stop-all.bat
```

### 手动启动

```bash
# 后端（在 backend 目录）
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python start.py             # 启动后端 http://localhost:8000

# 前端（在 frontend 目录）
cd frontend
npm install
npm run dev                 # 启动前端 http://localhost:5173

# Electron（在项目根目录，需先启动后端和前端）
cd ..
npm start
```

### 访问地址

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 默认账号

| 用户名 | 密码 |
|--------|------|
| admin | admin123 |

> **建议首次登录后修改默认密码。** 生产环境部署前请执行 `python scripts/maintenance/force_password_change.py` 强制所有默认账号改密。

## 技术栈

### 后端

- **框架**：FastAPI
- **ORM**：SQLAlchemy
- **数据库**：SQLite（`backend/data/rural_revitalization.db`）
- **认证**：JWT + bcrypt
- **缓存**：diskcache（本地磁盘）
- **打包**：PyInstaller

### 前端

- **框架**：Vue 3
- **语言**：TypeScript
- **构建**：Vite
- **UI 库**：Element Plus
- **状态**：Pinia
- **地图**：Leaflet
- **图表**：ECharts

### 桌面

- **壳**：Electron
- **打包**：electron-builder（Windows NSIS/Linux DEB）

> 具体版本号参见 `backend/requirements.txt`、`frontend/package.json` 和 `package.json`。

## 核心功能

| 模块 | 功能 |
|------|------|
| 帮扶村管理 | 基础信息、年度数据、地图可视化 |
| 帮扶学校管理 | 学校档案、学生资助 |
| 帮扶项目管理 | 项目全生命周期、进度跟踪 |
| 经费管理 | 资金台账、审批工作流 |
| 乡村工作 | 任务、日志、AI分析 |
| 数据同步 | 增量导入导出、多机协同 |
| 离线地图 | 瓦片下载、离线使用 |
| 系统管理 | 用户、角色、权限、审计日志 |

## 项目结构

```
.
├── backend/                 # 后端（Python + FastAPI）
│   ├── app/               # 应用代码
│   │   ├── api/v1/       # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # ORM 模型
│   │   ├── schemas/      # Pydantic 模式
│   │   ├── services/     # 业务服务
│   │   └── utils/        # 工具函数
│   ├── tests/            # 测试代码
│   └── data/             # 数据库文件
├── frontend/               # 前端（Vue 3 + TypeScript）
│   └── src/              # 源代码
├── electron/               # Electron 主进程
├── scripts/                # 脚本
└── docs/                   # 文档
```

## 测试

```bash
# 后端测试
cd backend && .venv\Scripts\python -m pytest tests/ -v

# 前端测试
cd frontend && npm test -- --run

# 代码质量
cd backend && .venv\Scripts\python -m flake8 app/ --max-line-length=120
cd frontend && npm run lint && npm run typecheck
```

## 构建安装包

```bash
# Windows 安装包（32位 + 64位）
scripts\build\build-installer-win.bat

# Windows 完整验证构建
scripts\build\build-installer-win-full.bat
```

## 文档

- [快速开始](docs/01-快速开始/QUICK_START.md)
- [安装指南](docs/01-快速开始/INSTALLATION_GUIDE.md)
- [用户手册](docs/01-快速开始/USER_GUIDE_FINAL.md)
- [部署指南](docs/04-部署文档/DEPLOYMENT_GUIDE.md)

---

**版本**: v1.2.0
**最后更新**: 2026-05-29
