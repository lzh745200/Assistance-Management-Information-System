# 系统恢复 & 地图增强 & 韧性机制 — 设计文档

**日期:** 2026-05-31  
**状态:** 已确认  
**目标平台:** Windows 开发机 → 麒麟 V10 ARM64 生产部署

---

## 1. 环境恢复方案

### 背景
D: 盘 NTFS 文件系统损坏导致：
- 200+ node_modules 文件 Permission denied
- `starlette/status.py` 含 2058 个 null bytes
- `rollup/parseAst.js` 代码行被随机字符替换
- pip install 成功但 site-packages 无实际写入

### 恢复步骤

```bash
# 1. 修复文件系统（管理员权限，可能需要重启）
chkdsk D: /F /X

# 2. 恢复项目文件
cd D:\military-Rural Revitalization-system
git checkout -- .

# 3. 重建前端
cd frontend
rmdir /s /q node_modules
npm install
npm run build

# 4. 重建后端 venv
cd backend
rmdir /s /q .venv .venv_corrupted
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 5. 验证
python start.py
# 访问 http://127.0.0.1:8000/health → {"status":"ok"}
```

### 预计耗时
- chkdsk: 5-30 分钟
- node_modules 重装: 3-5 分钟
- venv 重建: 2-3 分钟
- 总计: 10-40 分钟

---

## 2. 地图功能完善

### 数据获取
从 DataV.GeoAtlas (https://datav.aliyun.com/portal/school/atlas/area_selector) 下载：
- 贵州省 9 个地州级 GeoJSON（Polygon + 名称 + 中心点）
- 88 个县市级 GeoJSON（Polygon + 名称 + 所属地州 + 中心点）

存储位置：
```
frontend/src/assets/geo/
├── guizhou_prefectures.json   ← 9 地州
└── guizhou_counties.json      ← 88 县市
```

### 交互流程

```
┌─────────────────────────────────────────┐
│  默认：9 地州视图                        │
│  ┌─────────────────────────────────┐    │
│  │  遵义市   铜仁市   毕节市        │    │
│  │      黔南州（点击下钻）          │    │
│  │  黔东南州  黔西南州  六盘水市    │    │
│  │  贵阳市   安顺市                │    │
│  └─────────────────────────────────┘    │
│          ↓ 点击黔南州                   │
│  ┌─────────────────────────────────┐    │
│  │  ← 返回  黔南州 12 县市          │    │
│  │  都匀市 长顺县 独山县 平塘县     │    │
│  │  罗甸县 惠水县 贵定县 福泉市     │    │
│  │  瓮安县 三都县 荔波县 龙里县     │    │
│  │  ● 帮扶村标记点（蓝色）          │    │
│  │  ▲ 学校标记点（绿色）            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### OfflineMap.vue 改动

| 改动 | 说明 |
|------|------|
| 加载两个 GeoJSON | `guizhou_prefectures.json` + `guizhou_counties.json` |
| `viewLevel` 状态 | `"prefecture"` ↔ `"county"` 切换 |
| `currentPrefecture` | 当前选中的地州名 |
| 点击地州 → 下钻 | ECharts click 事件 → `emit('region-click', {name, code})` → 父组件调用 `drillDown(name)` |
| 返回按钮 | 模板内 toolbar 按钮，点击回到地州视图 |
| 县市悬浮提示 | `{县名} - 帮扶村: N 个` |

### 坐标定位（已实现）
- `index.vue` 工具栏输入框 → `parseCoordinate()` → 红点 pin 标记
- 流程: 输入 "26.5,107.5" → 回车 → 地图居中 + 红色 pin

### 路线计算（已实现）
- `utils/geo.ts`: `calculateRoute(origin, dest)` → Haversine 距离 × 1.5 道路系数 ÷ 35km/h
- `index.vue`: "计算到全部帮扶点的路线" 按钮 → 遍历所有村/校 → `routeLines` → ECharts lines series
- 显示: 虚线箭头 + 中段标签 "{时间}" + 摘要栏（最近/最远）

---

## 3. 系统韧性机制

### 3.1 启动前自检（`start.py` 增强）

```
start.py 启动流程:
├── _check_vcruntime()           ← 已有
├── _check_dependencies()        ← 新增
│   └── 对比 pip freeze vs requirements.txt
│       不一致 → WARNING + 提示运行 recovery
├── _verify_file_integrity()     ← 新增
│   └── 抽检 10 个关键 .py/.js 文件是否含 null bytes
│       损坏 → WARNING
├── _check_database_integrity()  ← 已有
└── _check_port_available()      ← 已有
```

关键原则：**仅警告，不阻塞启动** — 离线军用系统必须可用优先。

### 3.2 一键恢复脚本

**Windows (`recovery.bat`):**
```batch
@echo off
echo === 系统恢复脚本 ===
echo 将重建 venv 和 node_modules，数据库会被备份
pause
mkdir backups\%date:~0,10% 2>nul
copy backend\data\*.db backups\%date:~0,10%\
rmdir /s /q backend\.venv
python -m venv backend\.venv
backend\.venv\Scripts\pip install -r backend\requirements.txt
cd frontend
rmdir /s /q node_modules
call npm install
call npm run build
cd ..
echo === 恢复完成 ===
```

**麒麟 (`recovery.sh`):**
```bash
#!/bin/bash
echo "=== 系统恢复脚本 ==="
read -p "确认重建环境? (y/n) " -n 1 -r
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
mkdir -p backups/$(date +%Y%m%d)
cp backend/data/*.db backups/$(date +%Y%m%d)/
rm -rf backend/.venv
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
cd frontend
rm -rf node_modules dist
npm install && npm run build
cd ..
echo "=== 恢复完成 ==="
```

---

## 4. 文件清单

| 文件 | 操作 | 所属方案 |
|------|------|----------|
| `frontend/src/assets/geo/guizhou_prefectures.json` | 新建 | 地图 |
| `frontend/src/assets/geo/guizhou_counties.json` | 新建 | 地图 |
| `frontend/src/components/map/OfflineMap.vue` | 修改 | 地图 |
| `frontend/src/views/analytics/map/index.vue` | 修改 | 地图 |
| `backend/app/core/preflight.py` | 新建（自检模块）| 韧性 |
| `backend/start.py` | 修改（调用自检）| 韧性 |
| `recovery.bat` | 新建 | 韧性 |
| `recovery.sh` | 新建 | 韧性 |

---

## 5. 军队安全审计（Bandit 集成）

### 背景
军队乡村振兴管理系统涉及敏感数据（帮扶村信息、经费拨付记录），需满足军用安全基线。

### 方案

| 项 | 说明 |
|------|------|
| **工具** | `bandit` — Python 安全静态分析工具（已在 requirements.txt 中） |
| **集成点** | `.pre-commit-config.yaml` + CI 流水线 |
| **配置** | `bandit.yaml` — 排除测试文件、放宽 B101（assert）用于测试 |
| **检查项** | SQL 注入、硬编码密码、pickle 反序列化、subprocess 注入、XSS、弱加密算法 |
| **执行** | `bandit -r backend/app/ -c bandit.yaml` |
| **阻断策略** | HIGH/Critical 级别阻断提交；Medium 警告但不阻断 |

### bandit.yaml 骨架
```yaml
skips: ["B101"]        # assert 在测试中允许
exclude_dirs: ["tests", ".venv", "migrations"]
severity_filter: ["HIGH"]
```

---

## 6. 数据隔离验证（Organization 多租户）

### 背景
`Organization` 模型用于数据权限隔离，不同组织创建的数据彼此不可见。

### 验证用例

| # | 场景 | 预期 |
|---|------|------|
| 1 | 组织 A 用户创建帮扶村 | 组织 A 用户可见，组织 B 用户不可见 |
| 2 | 组织 A 用户查询经费列表 | 仅返回组织 A 的经费记录 |
| 3 | 管理员查询全部数据 | 可跨组织查看所有记录 |
| 4 | 无组织的用户（organization_id=NULL）| 仅看到无组织归属的数据 |
| 5 | 跨组织数据导出 | 普通用户仅导出本组织数据 |

### 实现
- 在 `tests/integration/` 下新增 `test_data_isolation.py`
- 创建两个组织 → 各创建一个用户 → 各创建一条帮扶村/经费记录 → 验证隔离
- 使用现有 `conftest.py` 的 `TestClient` + 内存 SQLite

---

## 7. 单机版离线容错

### 背景
系统在完全离线、本机回环环境下运行。外部依赖（Redis、SMTP、第三方 API）均不可用。

### 增强点

| 模块 | 当前状态 | 增强 |
|------|----------|------|
| Redis | `REDIS_ENABLED=False` 时跳过 | 连接失败时自动降级，写入日志，不抛异常 |
| SMTP/邮件 | 配置为空时跳过 | 同上 — 优雅降级 |
| 地图瓦片 | 在线获取 Gaode 瓦片 | 离线时显示纯色背景 + "离线模式" 水印 |
| 数据备份 | 定时 APScheduler 任务 | 备份失败时重试 3 次 → 写入错误日志 → 不中断服务 |
| 数据库锁 | SQLite 单连接 | 增加 WAL 模式 + 5 秒 busy_timeout |

### 离线提示
前端全局组件：当 `navigator.onLine === false` 时显示离线模式图标（或利用后端 API `/health` 探测）。

---

## 8. 回滚验证脚本

### 背景
每次修改后需快速确认核心功能未回归。

### 脚本结构（`scripts/verify_no_regression.py`）

```python
"""
回滚验证脚本 — 核心功能冒烟测试
用法: python scripts/verify_no_regression.py
"""
# 1. 认证 — 登录获取 token
# 2. CRUD — 帮扶村 创建/读取/更新/删除
# 3. CRUD — 经费 创建/读取/更新
# 4. 查询 — 组织列表、学校列表、项目列表
# 5. 地图 — /api/v1/map/markers, /api/v1/map/config
# 6. 中间件 — POST camelCase body 验证自动转换
# 7. 健康检查 — /health

# 输出: [PASS] 7/7  或  [FAIL] 2/7 (详细失败列表)
# 退出码: 0 = 全通过, 1 = 有失败
```

### 调用时机
- `recovery.bat/sh` 最后一步
- git pre-push hook 可选手动触发
- CI 流水线每 commit 自动运行

---

## 9. 更新后文件清单

| 文件 | 操作 | 所属方案 |
|------|------|----------|
| `bandit.yaml` | 新建 | 安全审计 |
| `tests/integration/test_data_isolation.py` | 新建 | 数据隔离 |
| `backend/app/core/preflight.py` | 新建 | 韧性 |
| `backend/start.py` | 修改 | 韧性 |
| `scripts/recovery.bat` | 新建 | 韧性 |
| `scripts/recovery.sh` | 新建 | 韧性 |
| `scripts/verify_no_regression.py` | 新建 | 回滚验证 |
| `frontend/src/assets/geo/guizhou_prefectures.json` | 新建 | 地图 |
| `frontend/src/assets/geo/guizhou_counties.json` | 新建 | 地图 |
| `frontend/src/components/map/OfflineMap.vue` | 修改 | 地图 |
| `frontend/src/views/analytics/map/index.vue` | 修改 | 地图 |
| `backend/app/services/redis_service.py` | 修改 | 离线容错 |
| `backend/app/services/email_service.py` | 修改 | 离线容错 |
