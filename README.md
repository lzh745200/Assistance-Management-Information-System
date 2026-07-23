# 帮扶管理信息系统

> 军民融合乡村振兴 — 完全离线的单机版桌面应用 | 多机协同数据同步 | v1.2.0

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20ARM64-orange)
![Tests](https://img.shields.io/badge/tests-11%2C600%2B-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-88%25-yellowgreen)

## 项目状态

| 指标 | 结果 |
|------|------|
| 后端测试 | **10,045 passed**, 0 skipped, 0 errors |
| 前端测试 | **1,624 passed**, 125 文件, 0 失败 |
| Flake8 | 0 错误, 0 警告 |
| ESLint | 0 错误, 0 警告 |
| Bandit (安全) | 0 高危 |
| vue-tsc | 0 错误 |
| TypeScript | strict: true（全选项启用） |
| Pre-commit | ruff（变更文件）+ flake8/bandit/vue-tsc（推送前） |
| CI/CD | PR Checks + Nightly Full Suite + Codecov |
| Sass | 1.101.0（modern-compiler API） |

> **上次全量验证**: 2026-07-22 — 全部 11,600+ 测试通过（后端 10,045 + 前端 1,624），零 lint 错误，零安全告警

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
- **代码质量**: ESLint + Prettier + lint-staged

### 桌面
- **壳**: Electron 33 + electron-builder
- **安装**: NSIS (Windows) / dpkg-deb (Linux ARM64)

## 测试体系

| 测试类型 | 工具 | 数量 | 覆盖范围 |
|---------|------|------|---------|
| 后端单元测试 | pytest | 10,045 | API/Service/Core/Model/Utils 全覆盖 |
| 后端集成测试 | pytest | 8 套 | Auth/Users/Policies/Search/Audit/API |
| 后端安全测试 | pytest | 3 套 | Data Isolation/Audit/Retry |
| 前端单元测试 | Vitest | 1,624 | API/Store/Component/Composable/Utils |
| E2E 测试 | Playwright | 12 流程 | Login/Dashboard/Projects/Approval/Funds |
| 性能测试 | Locust | 配置可用 | 负载测试 |
| 属性测试 | fast-check | 多组 | 组件属性验证 |
| 无障碍测试 | Vitest | 多组 | ARIA/键盘/颜色对比度 |
| 安全扫描 | Bandit | 0 高危 | SQL注入/密码/加密 |
| 代码检查 | Flake8/ESLint | 0 错误 | Python + Vue/TS |

### 运行测试

```bash
# 后端
cd backend && pytest tests/ -q --tb=short

# 前端
cd frontend && npm test

# 全量（不含 E2E）
make test

# E2E (Docker)
docker compose -f docker-compose.yml -f docker/docker-compose.e2e.yml --profile e2e up

# 覆盖率
cd backend && pytest --cov=app --cov-report=html
cd frontend && npm run test:coverage
```

## 开发工具链

```bash
# 代码格式化与检查
cd frontend && npm run lint            # ESLint 自动修复
cd frontend && npm run type-check      # TypeScript 类型检查
cd backend && flake8 app/ --max-line-length=120
cd backend && bandit -r app/

# Pre-commit hooks（推荐安装）
pip install pre-commit && pre-commit install
npx lint-staged                        # 仅检查暂存文件

# 构建
make build-win-x64                     # Windows x64 安装包
make build-kylin                       # 麒麟 V10 ARM64 DEB
```

## CI/CD 流水线

| 流水线 | 触发条件 | 内容 |
|--------|---------|------|
| **PR Checks** | Pull Request | 后端测试(50%覆盖门禁) + 前端测试 + flake8 + npm audit + SBOM |
| **Nightly Full** | 每日凌晨2:00 UTC | 全量测试 + 覆盖率报告 + Codecov + JUnit 报告 |
| **Build Windows** | Push main / tag v* | PyInstaller + electron-builder NSIS |
| **Build ARM64** | Push main / tag v* | Docker Buildx QEMU + electron-builder DEB |

## 项目结构

```
├── backend/app/              # 后端（FastAPI）
│   ├── api/v1/               # API 路由（42 个路由模块）
│   ├── core/                 # 核心：config, security, database, transaction, cache
│   ├── models/               # SQLAlchemy 数据模型（~40 个）
│   ├── services/             # 业务逻辑层（~60 个服务）
│   └── middleware/            # CSRF, 审计, 请求日志, 零信任
├── frontend/src/             # 前端（Vue 3 + TypeScript）
│   ├── views/                # 页面视图（~90 个组件）
│   ├── components/           # 通用 + 业务组件（~60 个）
│   ├── stores/               # Pinia 状态（18 个 store）
│   ├── composables/          # 组合式函数（~22 个）
│   └── utils/                # 工具函数（~40 个模块）
├── electron/                 # Electron 桌面壳
├── docker/                   # 多架构 Dockerfile + E2E compose
├── deploy/                   # 麒麟 V10 systemd + DEBIAN 配置
├── k8s/                      # Kubernetes 部署清单
├── nginx/                    # Nginx 反向代理配置
├── scripts/                  # 管理/运维脚本
├── build-scripts/            # electron-builder NSIS 钩子 + 构建配置
├── docs/                     # 项目文档
├── .github/workflows/        # CI/CD（PR Checks + Nightly + Build）
└── resources/                # 图标、VC++ 运行库、预置数据库
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

Copyright © 2025 贵州省军民融合乡村振兴项目组
