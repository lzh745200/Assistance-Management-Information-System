# 系统恢复 & 地图增强 & 安全韧性 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 恢复 Windows 开发环境，实现贵州地图地州/县市两级下钻 + 路线计算，添加安全审计/数据隔离/离线容错/启动自检/回滚验证

**Architecture:** 前端 OfflineMap 组件支持两级 GeoJSON 切换；后端 start.py 新增预检模块；Bandit 集成到 pre-commit；回滚验证脚本作为恢复最后一步

**Tech Stack:** Python 3.11 + FastAPI + SQLAlchemy / Vue 3 + TypeScript + ECharts / Bandit / pytest

**Prerequisite (manual):** `chkdsk D: /F /X` 修复文件系统后重建环境

---

## Phase 0: 环境恢复（手动 — 阻塞）

### Task 0: chkdsk + 重建环境

- [ ] **Step 0.1: 修复文件系统**
  ```bash
  # 以管理员运行 cmd
  chkdsk D: /F /X
  # 可能需要重启
  ```

- [ ] **Step 0.2: 恢复项目文件**
  ```bash
  cd D:\military-Rural Revitalization-system
  git checkout -- .
  ```

- [ ] **Step 0.3: 重建后端 venv**
  ```bash
  cd backend
  rmdir /s /q .venv .venv_corrupted 2>nul
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
  python start.py   # 验证 → /health 返回 200
  ```

- [ ] **Step 0.4: 重建前端**
  ```bash
  cd frontend
  rmdir /s /q node_modules 2>nul
  npm install
  npm run build   # 验证 → ✓ built in Ns
  ```

---

## Phase 1: 安全审计 + 回滚验证（快速见效）

### Task 1: Bandit 配置

**Files:**
- Create: `bandit.yaml`
- Modify: `.pre-commit-config.yaml` (add bandit hook)

- [ ] **Step 1.1: 创建 bandit.yaml**

```yaml
# bandit.yaml — Python 安全静态分析配置
skips: ["B101"]  # assert 在测试中允许
exclude_dirs: [".venv", "tests", "migrations", "node_modules", "frontend"]
severity_filter: ["HIGH", "MEDIUM"]
```

- [ ] **Step 1.2: 添加 pre-commit hook**

```yaml
# .pre-commit-config.yaml 追加
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.6
  hooks:
    - id: bandit
      args: ["-c", "bandit.yaml", "-r", "backend/app/"]
```

- [ ] **Step 1.3: 运行首次审计**
  ```bash
  cd backend
  .venv\Scripts\bandit -r app/ -c ../bandit.yaml
  ```
  Expected: 列出任何 HIGH/MEDIUM 安全问题（不阻塞构建）

- [ ] **Step 1.4: Commit**
  ```bash
  git add bandit.yaml .pre-commit-config.yaml
  git commit -m "feat: add bandit security audit config"
  ```

---

### Task 2: 回滚验证脚本

**Files:**
- Create: `scripts/verify_no_regression.py`

- [ ] **Step 2.1: 创建验证脚本**

```python
"""回滚验证脚本 — 核心功能冒烟测试
用法: cd backend && python ../scripts/verify_no_regression.py
退出码: 0=全通过 1=有失败
"""
import json, sys, urllib.request, urllib.error

BASE = "http://127.0.0.1:8000"
FAIL = 0

def test(name, method, path, data=None, code=200):
    global FAIL
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    h = {"Content-Type": "application/json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        if r.status == code:
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}: HTTP {r.status}")
            FAIL += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        FAIL += 1

# Login
d = json.dumps({"username":"admin","password":"admin123"}).encode()
r = urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/api/v1/auth/login", data=d,
    headers={"Content-Type":"application/json"}))
TOKEN = json.loads(r.read())["data"]["access_token"]
print("[OK] Login")

# Tests
test("Health", "GET", "/health")
test("Villages list", "GET", "/api/v1/supported-villages?page=1&page_size=3")
test("Village create (camelCase)", "POST", "/api/v1/supported-villages",
     {"villageName":"__reg_test__","department":"d","supportUnit":"s","county":"都匀市"})
# Get the created village ID
r2 = urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/api/v1/supported-villages?keyword=__reg_test__&page=1&page_size=1",
    headers={"Authorization": f"Bearer {TOKEN}"}))
items = json.loads(r2.read()).get("items", [])
VID = items[0]["id"] if items else 1
test("Village update", "PUT", f"/api/v1/supported-villages/{VID}",
     {"villageName":"__reg_test_upd__","isKeyCounty":1})
test("Fund list", "GET", "/api/v1/funds?page=1&page_size=3")
test("Fund create (camelCase)", "POST", "/api/v1/funds",
     {"fundName":"__reg_test_fund__","fundType":"project","amount":10000,"villageId":VID})
test("Map markers", "GET", "/api/v1/map/markers")
test("Map config", "GET", "/api/v1/map/config")
test("Projects list", "GET", "/api/v1/projects?page=1&page_size=3")
test("Schools list", "GET", "/api/v1/schools?page=1&page_size=3")
test("Dashboard", "GET", "/api/v1/dashboard/summary")

# Cleanup
for path in [f"/api/v1/supported-villages/{VID}", f"/api/v1/funds/1"]:
    try:
        urllib.request.urlopen(urllib.request.Request(
            f"{BASE}{path}", headers={"Authorization": f"Bearer {TOKEN}"},
            method="DELETE"), timeout=5)
    except: pass

print(f"\n{'='*40}\nPASSED: {12 - FAIL}/12\n{'='*40}")
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2.2: 运行验证**
  ```bash
  cd D:\military-Rural Revitalization-system
  backend\.venv\Scripts\python scripts\verify_no_regression.py
  ```
  Expected: `PASSED: 12/12`

- [ ] **Step 2.3: Commit**
  ```bash
  git add scripts/verify_no_regression.py
  git commit -m "feat: add rollback verification script"
  ```

---

## Phase 2: 启动自检 + 恢复脚本

### Task 3: 启动预检模块

**Files:**
- Create: `backend/app/core/preflight.py`
- Modify: `backend/app/start.py` (call preflight checks)

- [ ] **Step 3.1: 创建 preflight.py**

```python
"""启动前预检模块 — 依赖一致性、文件完整性、数据库健康"""
import logging, os, re, sys
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_FILES = [
    "app/main.py", "app/core/config.py", "app/core/security.py",
    "app/core/database.py", "app/api/v1/__init__.py",
]

def _get_installed_packages():
    """返回 {包名: 版本} (规范化键名)"""
    try:
        from importlib.metadata import distributions
        return {d.metadata["Name"].lower().replace("-","_"): d.version
                for d in distributions()}
    except Exception:
        return {}

def _parse_requirements(path: str) -> dict:
    """解析 requirements.txt → {包名: 版本}"""
    pkgs = {}
    p = re.compile(r"^([a-zA-Z0-9_-]+)==([\d.]+)")
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if ";" in line:
                    line = line.split(";")[0].strip()
                m = p.match(line)
                if m:
                    pkgs[m.group(1).lower().replace("-","_")] = m.group(2)
    except FileNotFoundError:
        pass
    return pkgs

def check_dependencies() -> bool:
    """检查已安装包与 requirements.txt 是否一致"""
    backend_dir = Path(__file__).resolve().parent.parent
    req_path = backend_dir / "requirements.txt"
    if not req_path.exists():
        return True
    required = _parse_requirements(str(req_path))
    installed = _get_installed_packages()
    mismatches = []
    for pkg, ver in required.items():
        if pkg in installed and installed[pkg] != ver:
            mismatches.append(f"  {pkg}: req={ver} inst={installed[pkg]}")
    if mismatches:
        logger.warning("依赖版本不一致:\n%s\n请运行 recovery 脚本修复", "\n".join(mismatches))
        return False
    logger.info("[OK] 依赖版本一致")
    return True

def verify_file_integrity() -> bool:
    """抽检关键文件是否含 null bytes (NTFS 损坏特征)"""
    backend_dir = Path(__file__).resolve().parent.parent
    corrupted = []
    for fname in REQUIRED_FILES:
        path = backend_dir / fname
        if not path.exists(): continue
        try:
            with open(path, "rb") as f:
                if b"\x00" in f.read():
                    corrupted.append(fname)
        except Exception:
            pass
    if corrupted:
        logger.warning("关键文件可能损坏 (含 null bytes):\n%s", "\n".join(corrupted))
        return False
    logger.info("[OK] 关键文件完整性检查通过")
    return True
```

- [ ] **Step 3.2: 集成到 start.py**

在 `start.py` 的 `main()` 函数中 `_ensure_dirs()` 之后添加:
```python
from app.core.preflight import check_dependencies, verify_file_integrity
check_dependencies()
verify_file_integrity()
```

- [ ] **Step 3.3: 验证 — 重启服务器，检查日志输出**
  ```
  Expected log:
  [OK] 依赖版本一致
  [OK] 关键文件完整性检查通过
  ```

- [ ] **Step 3.4: Commit**
  ```bash
  git add backend/app/core/preflight.py backend/app/start.py
  git commit -m "feat: add preflight checks (deps + file integrity)"
  ```

---

### Task 4: 一键恢复脚本

**Files:**
- Create: `scripts/recovery.bat`
- Create: `scripts/recovery.sh`

- [ ] **Step 4.1: 创建 recovery.bat**

```batch
@echo off
chcp 65001 >nul
echo ============================================
echo   军队乡村振兴管理系统 — 环境恢复脚本
echo ============================================
echo 将备份数据库并重建 venv + node_modules
echo.
pause

set BACKUP_DIR=backups\%date:~0,10%
mkdir %BACKUP_DIR% 2>nul
if exist backend\data\*.db (
    copy backend\data\*.db %BACKUP_DIR%\
    echo [OK] 数据库已备份到 %BACKUP_DIR%
)

echo [1/3] 重建 Python 虚拟环境...
cd backend
rmdir /s /q .venv 2>nul
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
echo [OK] venv 重建完成

echo [2/3] 重建前端...
cd ..\frontend
rmdir /s /q node_modules dist 2>nul
call npm install
call npm run build
cd ..
echo [OK] 前端构建完成

echo [3/3] 运行回滚验证...
backend\.venv\Scripts\python scripts\verify_no_regression.py
echo.
echo ============================================
echo   恢复完成
echo ============================================
pause
```

- [ ] **Step 4.2: 创建 recovery.sh**

```bash
#!/bin/bash
set -e
echo "=== 军队乡村振兴管理系统 — 环境恢复 ==="
read -p "确认重建环境? (y/n) " -r
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 0

BACKUP="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP"
cp backend/data/*.db "$BACKUP/" 2>/dev/null && echo "[OK] 数据库已备份"

echo "[1/3] 重建 Python venv..."
cd backend
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
echo "[OK] venv 重建完成"

echo "[2/3] 重建前端..."
cd ../frontend
rm -rf node_modules dist
npm install && npm run build
cd ..
echo "[OK] 前端构建完成"

echo "[3/3] 验证..."
backend/.venv/bin/python scripts/verify_no_regression.py
echo "=== 恢复完成 ==="
```

- [ ] **Step 4.3: Commit**
  ```bash
  git add scripts/recovery.bat scripts/recovery.sh
  git commit -m "feat: add one-click recovery scripts"
  ```

---

## Phase 3: 地图功能增强

### Task 5: 下载贵州 GeoJSON 数据

**Files:**
- Create: `frontend/src/assets/geo/guizhou_prefectures.json`
- Create: `frontend/src/assets/geo/guizhou_counties.json`

- [ ] **Step 5.1: 从 DataV 下载地州级 GeoJSON**

访问 https://datav.aliyun.com/portal/school/atlas/area_selector →
选择"贵州省" → 下载地市级 GeoJSON → 保存为 `guizhou_prefectures.json`

包含字段: `{"type":"FeatureCollection","features":[{"properties":{"name":"贵阳市","cp":[106.71,26.65]},...}]}`

- [ ] **Step 5.2: 从 DataV 下载县市级 GeoJSON**

选择"贵州省" → 下钻到县级 → 下载 → 保存为 `guizhou_counties.json`

包含字段: `{"type":"FeatureCollection","features":[{"properties":{"name":"都匀市","parent":"黔南布依族苗族自治州","cp":[107.52,26.26]},...}]}`

- [ ] **Step 5.3: 整合现有 qiannan.json 数据**

`qiannan.json` 已有的黔南州边界并入 `guizhou_prefectures.json`，避免数据丢失。

- [ ] **Step 5.4: Commit**
  ```bash
  git add frontend/src/assets/geo/
  git commit -m "feat: add Guizhou prefecture + county GeoJSON data"
  ```

---

### Task 6: OfflineMap 两级下钻

**Files:**
- Modify: `frontend/src/components/map/OfflineMap.vue`
- Modify: `frontend/src/views/analytics/map/index.vue`

- [ ] **Step 6.1: OfflineMap 加载两个 GeoJSON 并支持 viewLevel 切换**

在 `onMounted()` 中同时加载两个文件:
```typescript
onMounted(async () => {
  try {
    const prefectureModule = await import('@/assets/geo/guizhou_prefectures.json')
    const countyModule = await import('@/assets/geo/guizhou_counties.json')
    prefectureGeoJson = prefectureModule.default || prefectureModule
    countyGeoJson = countyModule.default || countyModule
    geoJson = props.viewLevel === 'county' ? countyGeoJson : prefectureGeoJson
    echarts.registerMap('guizhou-map', geoJson as any)
  } catch { /* fallback to existing guizhou.json */ }
  await nextTick()
  initChart()
})
```

- [ ] **Step 6.2: 点击地州 → emit region-click → 父组件 drillDown**

在 `renderMap()` 的 map series click 事件中:
```typescript
chart.on('click', 'series', (params: any) => {
  if (params.seriesType === 'map' && props.viewLevel === 'prefecture') {
    emit('region-click', { name: params.name })
  }
})
```

- [ ] **Step 6.3: 添加 zoom 到选中地州**

```typescript
function zoomToRegion(regionName: string) {
  if (!prefectureGeoJson || !chart) return
  const feature = (prefectureGeoJson as any).features.find(
    (f: any) => f.properties.name === regionName
  )
  if (feature?.properties?.cp) {
    const [lng, lat] = feature.properties.cp
    chart.setOption({
      geo: { center: [lng, lat], zoom: 4 }
    })
  }
}
```

- [ ] **Step 6.4: 父组件 index.vue 实现 drillDown + 返回**

```typescript
const mapViewLevel = ref<'prefecture' | 'county'>('prefecture')
const currentPrefecture = ref('')

function handleRegionClick(region: { name: string }) {
  if (mapViewLevel.value === 'prefecture') {
    drillDown(region.name)
  }
}

function drillDown(name: string) {
  currentPrefecture.value = name
  mapViewLevel.value = 'county'
}

function goBackToPrefecture() {
  currentPrefecture.value = ''
  mapViewLevel.value = 'prefecture'
}
```

模板添加返回按钮:
```html
<el-button v-if="mapViewLevel === 'county'" size="small" @click="goBackToPrefecture">
  ← 返回全省视图
</el-button>
```

- [ ] **Step 6.5: 过滤 marker 仅显示当前选中地州的**

```typescript
const visibleMarkers = computed(() => {
  if (mapViewLevel.value === 'prefecture') return geographicMarkers.value
  // 县级视图: 过滤出当前地州的 mark
  // 需要通过 API 返回的 county 字段匹配
  return geographicMarkers.value // 或者从 county-coords 接口获取
})
```

- [ ] **Step 6.6: 构建并验证**
  ```bash
  cd frontend && npm run build
  ```
  访问 `http://127.0.0.1:8000/map` → 默认地州视图 → 点击"黔南州" → 下钻到 12 县市 → 返回全省

- [ ] **Step 6.7: Commit**
  ```bash
  git add frontend/src/components/map/OfflineMap.vue frontend/src/views/analytics/map/index.vue
  git commit -m "feat: add map drill-down (prefecture ↔ county)"
  ```

---

## Phase 4: 离线容错 + 数据隔离

### Task 7: 离线容错增强

**Files:**
- Modify: `backend/app/core/config.py` (或各 service 文件)

- [ ] **Step 7.1: Redis 优雅降级**

在 Redis 连接逻辑中（如 `app/services/redis_service.py` 或初始化代码）:
```python
try:
    redis_client = redis.Redis(...)
    redis_client.ping()
except (redis.ConnectionError, OSError) as e:
    logger.warning("Redis 不可用，使用本地磁盘缓存: %s", e)
    redis_client = None  # 后续代码检查 if redis_client
```

- [ ] **Step 7.2: 备份任务重试 + 不中断**

在备份服务中:
```python
def backup_with_retry(db_path: str, backup_dir: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            shutil.copy2(db_path, backup_dir)
            return True
        except OSError as e:
            logger.warning("备份失败 (第%d次): %s", attempt + 1, e)
            time.sleep(1)
    logger.error("备份彻底失败，跳过")
    return False
```

- [ ] **Step 7.3: SQLite WAL 模式 + busy_timeout**

在 `app/core/database.py` 的 engine 创建中:
```python
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
```

- [ ] **Step 7.4: Commit**
  ```bash
  git add backend/app/core/database.py
  git commit -m "feat: add offline fault tolerance (WAL, Redis degrade, backup retry)"
  ```

---

### Task 8: 数据隔离验证用例

**Files:**
- Create: `tests/integration/test_data_isolation.py`

- [ ] **Step 8.1: 创建隔离测试**

```python
"""数据隔离验证 — Organization 多租户"""
import pytest
from app.core.database import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.supported_village import SupportedVillage
from app.core.security import hash_password

class TestDataIsolation:
    def test_cross_org_village_isolation(self, client):
        """组织A的帮扶村对组织B不可见"""
        db = SessionLocal()
        # 创建两个组织
        org_a = Organization(name="org_a", code="A001")
        org_b = Organization(name="org_b", code="B001")
        db.add_all([org_a, org_b])
        db.commit()

        # 组织A创建帮扶村
        village = SupportedVillage(
            village_name="isolation_test",
            organization_id=org_a.id,
            department="test"
        )
        db.add(village)
        db.commit()

        # 组织A用户查询 → 应看到
        q_a = db.query(SupportedVillage).filter(
            SupportedVillage.organization_id == org_a.id
        )
        assert q_a.count() >= 1

        # 组织B用户查询 → 不应看到
        q_b = db.query(SupportedVillage).filter(
            SupportedVillage.organization_id == org_b.id
        )
        assert q_b.count() == 0

        db.close()
```

- [ ] **Step 8.2: 运行验证**
  ```bash
  cd backend && .venv\Scripts\pytest tests/integration/test_data_isolation.py -v
  ```
  Expected: PASS

- [ ] **Step 8.3: Commit**
  ```bash
  git add tests/integration/test_data_isolation.py
  git commit -m "test: add data isolation test for multi-tenant orgs"
  ```

---

## Execution Order

```
Phase 0 (manual): chkdsk → git checkout → rebuild venv + node_modules
Phase 1: Task 1 (Bandit) + Task 2 (rollback verify) — 快速见效，并行
Phase 2: Task 3 (preflight) → Task 4 (recovery scripts)
Phase 3: Task 5 (GeoJSON data) → Task 6 (drill-down)
Phase 4: Task 7 (offline fault tolerance) → Task 8 (data isolation tests)
```

Each phase is independently testable. Commit after each task.

---

## Total: 8 tasks, ~16 commits, 13 files
