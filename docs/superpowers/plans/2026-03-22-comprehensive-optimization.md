# 全面优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 分四阶段全面优化系统稳定性、性能和用户体验，消除页面报错和显示异常。

**Architecture:** 先统一后端错误响应格式（两套冲突格式合并为一套），同步更新前端拦截器；再优化性能缺口；再完善前端体验；最后对12个功能模块逐一深度审查修复。

**Tech Stack:** Python FastAPI + SQLAlchemy + SQLite, Vue 3 + TypeScript + Element Plus + Axios, Electron 28

**Spec:** `docs/superpowers/specs/2026-03-22-comprehensive-optimization-design.md`

---

## 关键背景知识

### 当前错误响应格式冲突

**全局异常处理器** (`backend/app/core/exceptions.py` `register_exception_handlers()`) 返回：
```json
{ "success": false, "error": "错误消息", "code": 5000, "path": "/api/v1/..." }
```

**response.py 函数** (`backend/app/core/response.py` `error_response()`) 返回：
```json
{ "code": 400, "message": "错误消息", "meta": { "timestamp": "...", "request_id": "..." } }
```

**统一目标**：全局异常处理器改用 `error_response()` 函数，统一为 `{ code, message, errors?, meta }` 格式。
注意：`error_response()` 不含 `data` 字段（错误响应不需要），只有 `code`、`message`、可选 `errors` 列表和 `meta`。

### 前端响应解包规则（不得破坏）

- 含 `access_token` → 直接透传
- 纯包装层 `{ data: X }`（无 items/total/message/success/code）→ 自动解包为 X
- 含 `items/total` 的分页响应 → 保留原始结构
- 含 `{ code, data, message }` → 保留原始结构，当前自动补充 `success` 字段

**⚠️ 关键副作用**：自动解包条件之一是"不含 `success` 字段"。若注释掉 `success` 补充逻辑，`{ code, message, data }` 响应将满足解包条件，导致 `data` 被提升为 `response.data`，破坏所有读取 `response.data.code` 的调用方。
解决方案：同步修改解包条件，将 `"success" in response.data` 改为 `"code" in response.data`，见 Task 2 Step 4。

---

## 文件映射

### 阶段一修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/core/exceptions.py` | 修改 | 全局异常处理器改用 `error_response()` |
| `backend/app/core/response.py` | 只读参考 | `error_response()` 返回 dict，无需修改，处理器自行指定 HTTP 状态码 |
| `frontend/src/api/request.ts` | 修改 | 错误路径统一读取 `message` 字段，移除多路兼容 |
| `backend/app/api/v1/system/backup.py` | 检查修改 | 补全异常处理 |
| `backend/app/api/v1/system/health.py` | 检查修改 | 补全异常处理 |
| `backend/app/api/v1/data/dashboard.py` | 检查修改 | 数据库空值处理 |
| `backend/app/api/v1/data/statistics.py` | 检查修改 | 分页边界处理 |

### 阶段二修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/core/database_indexes.py` | 修改 | 补充缺失索引 |
| `backend/app/api/v1/organization.py` | 修改（待扫描确认） | 组织机构列表缓存 |
| `backend/app/api/v1/policy.py` | 修改（待扫描确认） | 政策列表缓存 |
| `backend/app/api/v1/villages.py` | 修改（待扫描确认） | 村庄基础信息缓存 |
| `backend/app/api/v1/data/reports.py` | 修改 | 强制分页 |

### 阶段三修改文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/api/request.ts` | 修改 | 错误提示中文化完善 |
| `frontend/src/views/*/` (多个) | 修改 | loading 状态 + 数据刷新 |

---

## 阶段一：后端稳定性层

---

### Task 1: 统一全局异常处理器响应格式

**Files:**
- Modify: `backend/app/core/exceptions.py`
- Modify: `backend/app/core/response.py`

- [ ] **Step 1: 阅读 response.py 的 error_response 函数签名**

```bash
grep -n "def error_response\|def server_error_response\|def not_found_response\|def unauthorized_response\|def forbidden_response\|def validation_error_response" "C:/military-Rural Revitalization-system/backend/app/core/response.py"
```

- [ ] **Step 2: 确认 `error_response()` 的返回格式**

`response.py` 的 `error_response()` 返回 dict `{code, message, errors?, meta}`，处理器自行选择 HTTP 状态码。`response.py` 本身**无需修改**，直接在 `exceptions.py` 各处理器中调用 `error_response()` 并传给 `JSONResponse` 即可。

- [ ] **Step 3: 修改 `exceptions.py` 的 `business_exception_handler`**

将：
```python
content = {
    "success": False,
    "error": exc.message,
    "code": exc.code,
    "path": request.url.path,
}
if exc.details:
    content["details"] = exc.details
return JSONResponse(status_code=http_status, content=content)
```

改为（在文件顶部添加 import）：
```python
from app.core.response import error_response
```

然后：
```python
# 注意：exc.details 是 dict 类型（见 BusinessError.__init__），结构因子类而异
# （如 NotFoundException.details = {"identifier": "xxx"}，ValidationError.details = {"field": "..."}）
# 与 validation_exception_handler 的 error_list 结构不同，此处仅用于 meta 透传，不保证 field/message 键存在
content = error_response(
    message=exc.message,
    code=exc.code,
    errors=[exc.details] if exc.details else None,
    request_id=request.headers.get("X-Request-ID"),
)
return JSONResponse(status_code=http_status, content=content)
```

- [ ] **Step 4: 修改 `http_exception_handler`**

```python
content = error_response(
    message=str(exc.detail),
    code=exc.status_code,
    request_id=request.headers.get("X-Request-ID"),
)
return JSONResponse(status_code=exc.status_code, content=content)
```

- [ ] **Step 5: 修改 `validation_exception_handler`**

```python
error_list = [{"field": e["field"], "message": e["message"], "code": e["type"]} for e in errors]
content = error_response(
    message="请求参数验证失败",
    code=422,
    errors=error_list,
    request_id=request.headers.get("X-Request-ID"),
)
return JSONResponse(status_code=422, content=content)
```

- [ ] **Step 6: 修改 `pydantic_validation_exception_handler`（同上格式）**

```python
error_list = [{"field": e["field"], "message": e["message"], "code": e["type"]} for e in errors]
content = error_response(
    message="数据验证失败",
    code=422,
    errors=error_list,
    request_id=request.headers.get("X-Request-ID"),
)
return JSONResponse(status_code=422, content=content)
```

- [ ] **Step 7: 修改 `integrity_exception_handler`**

```python
content = error_response(
    message=error_msg,
    code=409,
    request_id=request.headers.get("X-Request-ID"),
)
return JSONResponse(status_code=409, content=content)
```

- [ ] **Step 8: 修改 `sqlalchemy_exception_handler`**

```python
content = error_response(
    message="数据库操作失败，请稍后重试",
    code=500,
    request_id=request.headers.get("X-Request-ID"),
)
return JSONResponse(status_code=500, content=content)
```

- [ ] **Step 9: 修改 `general_exception_handler`**

原函数中 `error_report_id`/`support_info` 的生成逻辑（后台线程报告）保持不变，只替换最终构建 `response_content` 的部分。

将原来的：
```python
response_content: dict = {
    "success": False,
    "error": "服务器内部错误,请稍后重试",
    "code": 7000 if error_report_id else 500,
    "path": request.url.path,
}
if _IS_DEBUG:
    response_content["exception_type"] = type(exc).__name__
    response_content["message"] = str(exc) if str(exc) else "未知错误"
if error_report_id and support_info:
    response_content["error_report_id"] = error_report_id
    response_content["support_info"] = support_info
return JSONResponse(status_code=500, content=response_content)
```

替换为：
```python
msg = "服务器内部错误，请稍后重试"
if _IS_DEBUG and str(exc):
    msg = f"{type(exc).__name__}: {exc}"

content = error_response(
    message=msg,
    code=7000 if error_report_id else 500,
    request_id=request.headers.get("X-Request-ID"),
)
# 保留严重错误报告信息（不变动原有逻辑）
if error_report_id and support_info:
    content["error_report_id"] = error_report_id
    content["support_info"] = support_info
if _IS_DEBUG:
    content["exception_type"] = type(exc).__name__

return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
```

- [ ] **Step 10: 验证后端可正常启动**

```bash
cd "C:/military-Rural Revitalization-system/backend"
python -c "from app.core.exceptions import register_exception_handlers; print('OK')"
```

Expected: `OK`

- [ ] **Step 11: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add backend/app/core/exceptions.py
git commit -m "fix: 统一全局异常处理器响应格式为 {code, message, errors?, meta}"
```

---

### Task 2: 更新前端响应拦截器适配统一格式

**Files:**
- Modify: `frontend/src/api/request.ts`

- [ ] **Step 1: 定位当前错误处理代码位置**

```bash
grep -n "detail\|error\.message\|success.*code\|code.*success\|resData" "C:/military-Rural Revitalization-system/frontend/src/api/request.ts" | head -50
```

- [ ] **Step 2: 更新 422 错误处理**

当前代码（约第403-418行）读取 `resData?.error?.message`（两层嵌套），需改为读取顶层 `message` 字段：
```typescript
// 422 验证错误
case 422: {
  const data = error.response?.data
  const msg = data?.message || '请求参数验证失败'  // 统一读取顶层 message，不再兼容 detail
  // 如有字段级错误列表
  if (data?.errors?.length) {
    const fieldErrors = data.errors.map((e: any) => `${e.field}: ${e.message}`).join('；')
    ElMessage.error(fieldErrors)
  } else {
    ElMessage.error(msg)
  }
  break
}
```

- [ ] **Step 3: 更新通用错误处理**

当前代码读取 `detail` 字段，改为只读取 `message` 字段（移除 `detail`，保留 `error` 作为过渡兼容）：
```typescript
// 通用错误
default: {
  const data = error.response?.data
  const msg = data?.message || data?.error || '请求失败'  // data?.error: 过渡期兼容旧 {success,error} 格式，Task 1 完成后可移除
  if (status !== 404 && status !== 405) {
    ElMessage.error(msg)
  }
}
```

- [ ] **Step 4: 修复 `success` 字段与自动解包的冲突（关键步骤）**

**背景**：自动解包条件检查"不含 `success` 字段"作为解包触发条件之一。如果直接注释 `success` 补充逻辑，会导致 `{ code, message, data }` 响应满足解包条件，将 `data` 字段提升为 `response.data`，破坏所有调用方。

**正确做法**：同步修改自动解包条件，将 `"success" in response.data` 替换为 `"code" in response.data`（含 `code` 的响应不解包），然后再注释掉 `success` 补充逻辑。

找到自动解包的判断条件（约第269-283行）：
```typescript
// 修改前（解包条件：不含 success 字段）
!Object.keys(response.data).some(k => ["items","total","access_token","message","success","code"].includes(k))

// 修改后（解包条件：不含 code 字段，这样 { code, message, data } 格式不会被解包；保留 message 防止旧接口误触发）
!Object.keys(response.data).some(k => ["items","total","access_token","message","code"].includes(k))
```

然后将 `success` 补充逻辑注释掉：
```typescript
// 不再需要：后端 success_response() 直接返回 success 字段
// if ("code" in response.data && !("success" in response.data)) {
//   response.data.success = response.data.code === 200;
// }
```

- [ ] **Step 5: 验证前端编译无错误**

```bash
cd "C:/military-Rural Revitalization-system/frontend"
npx tsc --noEmit 2>&1 | head -30
```

Expected: 无 TypeScript 错误

- [ ] **Step 6: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add frontend/src/api/request.ts
git commit -m "fix: 前端响应拦截器统一读取 message 字段，移除多路字段兼容"
```

---

### Task 3: 扫描并修复 system/ 和 data/ 下异常捕获缺口

**Files:**
- Modify: `backend/app/api/v1/system/backup.py`
- Modify: `backend/app/api/v1/system/health.py`
- Modify: `backend/app/api/v1/data/dashboard.py`
- Modify: `backend/app/api/v1/data/statistics.py`
- Modify: `backend/app/api/v1/data/reports.py`

- [ ] **Step 1: 扫描 system/ 下无异常处理的路由**

```bash
grep -n "^async def\|^def " "C:/military-Rural Revitalization-system/backend/app/api/v1/system/backup.py" | head -20
grep -n "try:\|except " "C:/military-Rural Revitalization-system/backend/app/api/v1/system/backup.py" | head -20
```

- [ ] **Step 2: 读取 backup.py 并修复缺少 try/except 的路由**

逐函数检查，对每个直接调用服务层而无 try/except 的路由函数添加：
```python
try:
    # 原有逻辑
    result = await service.do_something()
    return success_response(data=result)
except BusinessError:
    raise  # BusinessError 由全局处理器处理
except Exception as e:
    logger.error(f"操作失败: {e}", exc_info=True)
    raise BusinessError(f"操作失败：{str(e)}", code=ErrorCode.DATABASE_ERROR, status_code=500)
```

- [ ] **Step 3: 扫描并修复 data/dashboard.py 的空值处理**

```bash
grep -n "\.first()\|\.one()\|\[0\]\|\.name\|\.value" "C:/military-Rural Revitalization-system/backend/app/api/v1/data/dashboard.py" | head -30
```

对所有 `.first()` 后直接访问属性的代码，添加 `if result is None` 检查：
```python
# 修复前
result = db.query(Model).filter(...).first()
return {"value": result.value}  # 若 result 为 None 则 AttributeError

# 修复后
result = db.query(Model).filter(...).first()
if result is None:
    return success_response(data={"value": None, "message": "暂无数据"})
return success_response(data={"value": result.value})
```

- [ ] **Step 4: 修复 statistics.py 的分页边界处理**

```bash
grep -n "page\|page_size\|offset\|limit" "C:/military-Rural Revitalization-system/backend/app/api/v1/data/statistics.py" | head -20
```

在接受分页参数的接口添加边界修正：
```python
# 添加在参数处理处
page = max(1, page)
page_size = min(max(1, page_size), 100)  # 最大100条/页
offset = (page - 1) * page_size
```

- [ ] **Step 5: 对 system/health.py 做同样的扫描和修复**

```bash
grep -n "^async def\|except\|try:" "C:/military-Rural Revitalization-system/backend/app/api/v1/system/health.py" | head -30
```

- [ ] **Step 6: 验证修改后导入无误**

```bash
cd "C:/military-Rural Revitalization-system/backend"
python -c "
from app.api.v1.system.backup import router as r1
from app.api.v1.system.health import router as r2
from app.api.v1.data.dashboard import router as r3
from app.api.v1.data.statistics import router as r4
print('所有模块导入成功')
"
```

- [ ] **Step 7: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add backend/app/api/v1/system/ backend/app/api/v1/data/
git commit -m "fix: 补全 system/ 和 data/ 接口异常捕获，修复 null 空值和分页边界问题"
```

---

### Task 4: 强化输入验证

**Files:**
- Modify: `backend/app/api/v1/projects.py`
- Modify: `backend/app/api/v1/funds.py`
- Modify: `backend/app/api/v1/organization.py`

- [ ] **Step 1: 扫描未使用 Pydantic 模型的 POST/PUT 接口**

```bash
grep -n "^async def.*post\|^async def.*put\|@router.post\|@router.put" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" | head -20
grep -n "Body\|Form\|request: Request" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" | head -10
```

- [ ] **Step 2: 检查 Pydantic Schema 是否有字段长度限制**

```bash
grep -rn "class.*Schema\|class.*Create\|class.*Update" "C:/military-Rural Revitalization-system/backend/app/schemas/" | head -20
grep -n "max_length\|min_length\|Field(" "C:/military-Rural Revitalization-system/backend/app/schemas/project.py" 2>/dev/null | head -20
```

- [ ] **Step 3: 对主要 Schema 添加字段长度约束**

找到 `schemas/` 目录下的 project.py、fund.py、organization.py，对字符串字段添加 `max_length`：
```python
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=200, description="项目名称")
    description: str = Field(default="", max_length=2000, description="项目描述")
    # ... 其他字段
```

- [ ] **Step 4: 验证 Schema 修改无误**

```bash
cd "C:/military-Rural Revitalization-system/backend"
python -c "from app.schemas.project import ProjectCreate; print('OK')"
```

- [ ] **Step 5: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add backend/app/schemas/
git commit -m "feat: Pydantic Schema 字段添加长度约束，强化输入验证"
```

---

## 阶段二：API 性能优化层

---

### Task 5: 慢查询排查与索引补充

**Files:**
- Modify: `backend/app/core/database_indexes.py`

- [ ] **Step 1: 查看现有索引定义**

```bash
grep -n "INDEX_DEFINITIONS\|idx_\|\"table\"" "C:/military-Rural Revitalization-system/backend/app/core/database_indexes.py" | head -50
```

- [ ] **Step 2: 扫描高频查询中的排序和过滤字段**

```bash
grep -rn "order_by\|filter.*created_at\|filter.*status\|filter.*org_id\|filter.*project_id" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" "C:/military-Rural Revitalization-system/backend/app/api/v1/funds.py" | head -30
```

- [ ] **Step 3: 与现有索引对比，找出缺失**

将扫描到的高频过滤字段与 `database_indexes.py` 中 `INDEX_DEFINITIONS` 对比，识别未覆盖的字段。

典型缺失场景：
- `projects.status` + `projects.created_at` 复合索引
- `funds.project_id` + `funds.status` 复合索引
- `audit_logs.created_at` 单列索引（大表时间范围查询）

- [ ] **Step 4: 在 INDEX_DEFINITIONS 中添加缺失索引**

```python
# 在 INDEX_DEFINITIONS 列表中追加：
("idx_projects_status_created", "projects", ["status", "created_at"]),
("idx_funds_project_status", "funds", ["project_id", "status"]),
# ... 根据实际扫描结果添加
```

- [ ] **Step 5: 扫描 N+1 查询（重点检查循环内查询）**

```bash
grep -rn "for.*in.*query\|\.query.*for\|append.*db\." "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" "C:/military-Rural Revitalization-system/backend/app/api/v1/funds.py" | head -20
```

- [ ] **Step 6: 修复发现的 N+1 查询**

将循环内查询改为 JOIN 或批量查询：
```python
# N+1 模式（修复前）
projects = db.query(Project).all()
for p in projects:
    p.org_name = db.query(Organization).filter_by(id=p.org_id).first().name

# 批量查询（修复后）
from sqlalchemy.orm import joinedload
projects = db.query(Project).options(joinedload(Project.organization)).all()
```

- [ ] **Step 7: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add backend/app/core/database_indexes.py backend/app/api/v1/
git commit -m "perf: 补充缺失数据库索引，修复 N+1 查询问题"
```

---

### Task 6: 缓存策略补充

**Files:**
- Modify: 高频接口文件（根据扫描结果确定）

- [ ] **Step 1: 查看现有缓存装饰器用法**

```bash
grep -rn "cache_manager\|@cache\|get_cached\|cache_key" "C:/military-Rural Revitalization-system/backend/app/api/v1/data/analytics.py" | head -20
```

- [ ] **Step 2: 识别高频访问、低变更接口**

候选接口（GET 接口，数据不频繁变更）：
```bash
grep -rn "@router.get" "C:/military-Rural Revitalization-system/backend/app/api/v1/organization.py" \
  "C:/military-Rural Revitalization-system/backend/app/api/v1/villages.py" \
  "C:/military-Rural Revitalization-system/backend/app/api/v1/policy.py" | head -20
```

- [ ] **Step 3: 为组织机构列表接口添加缓存**

组织机构数据变更频率低，适合5分钟缓存：
```python
from app.core.cache import cache_manager

@router.get("/")
async def list_organizations(...):
    # 使用固定缓存键（非动态），便于更新时清除
    cache_key = "orgs:list"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    # 原有查询逻辑
    result = ...
    cache_manager.set(cache_key, result, ttl=300)
    return result
```

- [ ] **Step 4: 为政策列表接口添加缓存（同上模式）**

- [ ] **Step 5: 为村庄基础信息接口添加缓存（同上模式）**

- [ ] **Step 6: 在数据更新接口（POST/PUT/DELETE）中清除相关缓存**

注意：`cache_manager` 只有 `delete(key: str)` 方法，**没有** `delete_pattern()`。需要使用固定键命名规范（不带动态参数），如 Step 3 所示。

```python
@router.post("/")
async def create_organization(...):
    # 创建逻辑...
    # 清除列表缓存（使用与 Step 3 相同的固定键）
    cache_manager.delete("orgs:list")
    return success_response(data=result)
```

- [ ] **Step 7: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add backend/app/api/v1/
git commit -m "perf: 为组织机构、政策、村庄接口添加5分钟缓存"
```

---

### Task 7: 接口响应精简

**Files:**
- Modify: `backend/app/api/v1/projects.py`
- Modify: `backend/app/api/v1/funds.py`

- [ ] **Step 1: 检查列表接口是否返回全字段**

```bash
grep -n "def.*list\|query.*all()\|\.all()" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" | head -20
```

- [ ] **Step 2: 为项目列表接口创建精简 Schema**

如果列表接口返回了 `description`（长文本）等详情字段，创建 `ProjectListItem` Schema 只包含列表所需字段：
```python
class ProjectListItem(BaseModel):
    id: int
    name: str
    status: str
    org_id: int
    created_at: datetime
    # 不包含 description、附件列表等详情字段

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 检查大数据量接口是否有分页**

```bash
grep -rn "\.all()\b" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" | grep -v "test\|#"
```

对无分页的 `.all()` 调用，添加 `limit(1000)` 硬限制或强制分页参数。

- [ ] **Step 4: 检查文件下载接口是否使用流式响应**

```bash
grep -rn "FileResponse\|StreamingResponse\|open.*rb" "C:/military-Rural Revitalization-system/backend/app/api/v1/" | head -10
```

将大文件下载改为 `StreamingResponse`（如已使用则跳过）。

- [ ] **Step 5: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add backend/app/api/v1/ backend/app/schemas/
git commit -m "perf: 列表接口精简返回字段，大数据量接口添加分页保护"
```

---

## 阶段三：前端体验优化层

---

### Task 8: 完善加载状态（可与阶段一并行）

**Files:**
- Modify: `frontend/src/views/projects/ProjectManagement.vue`
- Modify: `frontend/src/views/funds/EnhancedList.vue`
- Modify: `frontend/src/views/analytics/dashboard/Dashboard.vue`

- [ ] **Step 1: 检查 ProjectManagement.vue 的加载状态**

```bash
grep -n "loading\|isLoading\|v-loading\|disabled" "C:/military-Rural Revitalization-system/frontend/src/views/projects/ProjectManagement.vue" | head -20
```

- [ ] **Step 2: 为无 loading 的数据请求添加加载状态**

对每个 `fetchXxx` 函数：
```typescript
const loading = ref(false)

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await api.getProjects()
    projects.value = res.data
  } finally {
    loading.value = false
  }
}
```

模板中：
```html
<el-table v-loading="loading" :data="projects">
```

- [ ] **Step 3: 为操作按钮（删除/保存/提交）添加防重复点击**

```html
<el-button :loading="submitting" :disabled="submitting" @click="handleSubmit">
  保存
</el-button>
```

```typescript
const submitting = ref(false)
const handleSubmit = async () => {
  if (submitting.value) return
  submitting.value = true
  try {
    await api.saveProject(form.value)
    ElMessage.success('保存成功')
  } finally {
    submitting.value = false
  }
}
```

- [ ] **Step 4: 对 Dashboard.vue 做同样处理**

- [ ] **Step 5: 对 funds/EnhancedList.vue 做同样处理**

- [ ] **Step 6: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add frontend/src/views/
git commit -m "feat: 主要页面添加加载状态和防重复提交"
```

---

### Task 9: 修复增删改后数据不刷新问题

**Files:**
- Modify: `frontend/src/views/projects/ProjectManagement.vue`
- Modify: `frontend/src/views/funds/EnhancedList.vue`
- Modify: `frontend/src/views/organization/Edit.vue`

- [ ] **Step 1: 扫描弹窗关闭后未刷新的模式**

```bash
grep -n "dialogVisible\|showDialog\|\.close\(\)\|ElDialog\|handleClose\|onClose" "C:/military-Rural Revitalization-system/frontend/src/views/projects/ProjectManagement.vue" | head -20
```

- [ ] **Step 2: 修复保存成功后不刷新列表**

模式：保存成功后调用 `fetchList()`：
```typescript
const handleSave = async () => {
  try {
    await api.saveProject(form.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchProjects()  // ← 确保有此行
  } catch (e) {
    // 错误由拦截器处理
  }
}
```

- [ ] **Step 3: 修复弹窗关闭后表单未重置**

```typescript
const handleDialogClose = () => {
  dialogVisible.value = false
  Object.assign(form, defaultForm)  // 重置表单到初始值
  formRef.value?.resetFields()      // 重置校验状态
}
```

- [ ] **Step 4: 对 funds/EnhancedList.vue 做同样检查和修复**

- [ ] **Step 5: 检查路由切换时组件状态清理**

```bash
grep -n "onUnmounted\|onBeforeUnmount\|watch.*route" "C:/military-Rural Revitalization-system/frontend/src/views/projects/ProjectManagement.vue" | head -10
```

若存在定时器或全局事件监听，确保在 `onUnmounted` 中清理。

- [ ] **Step 6: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add frontend/src/views/
git commit -m "fix: 修复增删改后列表不刷新、弹窗关闭后表单未重置问题"
```

---

### Task 10: 表单交互优化

**Files:**
- Modify: `frontend/src/views/projects/Edit.vue`
- Modify: `frontend/src/views/funds/Edit.vue`

- [ ] **Step 1: 检查表单校验规则是否实时触发**

```bash
grep -n "trigger\|blur\|change\|rules" "C:/military-Rural Revitalization-system/frontend/src/views/projects/Edit.vue" | head -20
```

- [ ] **Step 2: 为必填字段添加 change 触发校验**

```typescript
const rules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: ['blur', 'change'] }
  ],
  // ...
}
```

- [ ] **Step 3: 确保提交失败后保留表单数据**

检查 `catch` 块中没有 `resetFields()` 调用（失败时不应重置数据）：
```typescript
const handleSubmit = async () => {
  try {
    await api.saveProject(form.value)
    // 成功才重置
    formRef.value?.resetFields()
  } catch (e) {
    // 失败：不重置表单，让用户修改后重试
    // 错误消息由拦截器统一处理
  }
}
```

- [ ] **Step 4: 统一日期选择器格式**

```bash
grep -n "DatePicker\|date-format\|value-format\|format=" "C:/military-Rural Revitalization-system/frontend/src/views/projects/Edit.vue" | head -10
```

确保所有日期选择器使用统一格式：`value-format="YYYY-MM-DD"`。

- [ ] **Step 5: Commit**

```bash
cd "C:/military-Rural Revitalization-system"
git add frontend/src/views/
git commit -m "feat: 表单实时校验、失败保留数据、日期格式统一"
```

---

## 阶段四：模块深度审查

> **审查流程**：每个模块按"阅读代码 → 测试操作路径 → 修复问题 → 提交"顺序执行。P1 问题（功能异常/数据错误/安全漏洞）必须在进入下一模块前修复。顺序为建议顺序，P1 阻塞时可并行审查后续模块，但必须在阶段结束前全部解决。

### 每模块通用审查 Checklist

每个模块审查时，必须检查以下5个维度：

| 维度 | 检查项 |
|------|--------|
| **代码质量** | 无未使用变量；无重复代码；函数职责单一（超过80行考虑拆分） |
| **错误处理** | 接口有 try/except；数据库 null 结果有防护；网络失败有提示 |
| **性能** | 无 N+1 查询；高频接口有缓存；无无限制 `.all()` |
| **用户体验** | 操作有 loading；成功/失败有提示；弹窗关闭后表单重置 |
| **安全性** | 查询有权限过滤（数据隔离）；输入有长度/类型校验；无 SQL 拼接 |

---

### Task 11: 审查模块1 - 用户认证与权限管理

**Files:**
- Review: `backend/app/api/v1/auth/`
- Review: `frontend/src/views/auth/LoginSafe.vue`
- Review: `frontend/src/stores/auth.ts`

- [ ] **Step 1: 阅读认证模块代码**

```bash
ls "C:/military-Rural Revitalization-system/backend/app/api/v1/auth/"
cat "C:/military-Rural Revitalization-system/backend/app/api/v1/auth/__init__.py"
```

- [ ] **Step 2: 检查 Token 过期处理**

前端 Token 刷新逻辑（在 request.ts 中已有）是否正确处理并发请求。检查 `stores/auth.ts` 的 logout 逻辑。

- [ ] **Step 3: 检查权限中间件覆盖**

```bash
grep -n "Depends\|require_permission\|get_current_user" "C:/military-Rural Revitalization-system/backend/app/api/v1/auth/" -r | head -20
```

确认所有需要鉴权的接口都有 `Depends(get_current_user)` 依赖。

- [ ] **Step 4: 验证操作路径**

手动测试：登录 → 刷新页面 → Token 过期后自动刷新 → 退出登录后无法访问接口。

- [ ] **Step 5: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 认证与权限模块问题修复"
```

---

### Task 12: 审查模块2 - 组织机构管理

**Files:**
- Review: `backend/app/api/v1/organization.py`
- Review: `frontend/src/views/organization/`

- [ ] **Step 1: 阅读组织机构接口**

```bash
grep -n "^@router\|^async def" "C:/military-Rural Revitalization-system/backend/app/api/v1/organization.py" | head -30
```

- [ ] **Step 2: 检查树形结构查询性能**

组织机构通常为树形结构，检查是否存在递归查询性能问题：
```bash
grep -n "parent_id\|children\|recursive\|WITH RECURSIVE" "C:/military-Rural Revitalization-system/backend/app/api/v1/organization.py" | head -10
```

- [ ] **Step 3: 验证组织机构 CRUD 操作**

测试：创建子组织 → 编辑 → 删除（含级联处理）。

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 组织机构模块问题修复"
```

---

### Task 13: 审查模块3 - 项目管理

**Files:**
- Review: `backend/app/api/v1/projects.py`
- Review: `backend/app/api/v1/project_milestones.py`
- Review: `frontend/src/views/projects/`

- [ ] **Step 1: 检查项目状态流转逻辑**

```bash
grep -n "status\|state\|transition" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" | head -20
```

- [ ] **Step 2: 检查项目与里程碑的关联查询**

```bash
grep -n "milestone\|JOIN\|relationship" "C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py" | head -10
```

- [ ] **Step 3: 验证项目 CRUD + 里程碑操作路径**

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 项目管理模块问题修复"
```

---

### Task 14: 审查模块4 - 资金管理

**Files:**
- Review: `backend/app/api/v1/funds.py`
- Review: `backend/app/api/v1/fund_budgets.py`
- Review: `backend/app/api/v1/fund_lifecycle.py`
- Review: `frontend/src/views/funds/`

- [ ] **Step 1: 检查资金计算精度**

```bash
grep -n "float\|decimal\|Decimal\|round\b" "C:/military-Rural Revitalization-system/backend/app/api/v1/funds.py" | head -20
```

资金计算应使用 `Decimal` 而非 `float`，避免精度问题。

- [ ] **Step 2: 检查资金状态流转和权限控制**

- [ ] **Step 3: 验证资金 CRUD + 预算 + 生命周期操作**

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 资金管理模块问题修复"
```

---

### Task 15: 审查模块5 - 人员管理

**Files:**
- Review: `backend/app/api/v1/` (people/personnel相关)
- Review: `frontend/src/views/` (personnel相关)

- [ ] **Step 1: 找到人员管理相关文件**

```bash
ls "C:/military-Rural Revitalization-system/backend/app/api/v1/" | grep -i "person\|personnel\|user\|member\|staff"
```

- [ ] **Step 2: 检查人员数据的权限隔离**

确认人员查询有数据范围控制（按组织机构隔离）。

- [ ] **Step 3: 验证人员 CRUD 操作路径**

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 人员管理模块问题修复"
```

---

### Task 16: 审查模块6 - 消息与通知（高风险）

**Files:**
- Review: `backend/app/api/v1/messages.py`
- Review: `backend/app/api/v1/messages_extended.py`
- Review: `frontend/src/views/message/`

- [ ] **Step 1: 检查消息读取权限**

```bash
grep -n "user_id\|sender\|receiver\|current_user" "C:/military-Rural Revitalization-system/backend/app/api/v1/messages.py" | head -20
```

确认用户只能读取自己的消息，不能读取他人消息。

- [ ] **Step 2: 检查消息发送的速率限制**

防止消息刷屏或恶意发送。

- [ ] **Step 3: 检查 Electron 通知轮询机制**

```bash
grep -n "polling\|setInterval\|60s\|60000" "C:/military-Rural Revitalization-system/frontend/src/composables/useMessageNotification.ts" | head -10
```

确认组件卸载时清理定时器。

- [ ] **Step 4: 验证消息操作路径**

测试：发送消息 → 接收通知 → 标记已读 → 消息中心显示。

- [ ] **Step 5: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 消息与通知模块问题修复"
```

---

### Task 17: 审查模块7 - 审批工作流（高风险）

**Files:**
- Review: `backend/app/api/v1/approval.py`
- Review: `frontend/src/views/approval/`

- [ ] **Step 1: 检查审批权限控制**

```bash
grep -n "approver\|permission\|current_user\|status" "C:/military-Rural Revitalization-system/backend/app/api/v1/approval.py" | head -30
```

确认只有指定审批人能批准/拒绝。

- [ ] **Step 2: 检查审批状态流转的原子性**

审批操作需防止并发提交导致的状态竞争：
```bash
grep -n "with_for_update\|lock\|SELECT.*FOR UPDATE" "C:/military-Rural Revitalization-system/backend/app/api/v1/approval.py" | head -10
```

- [ ] **Step 3: 验证审批操作路径**

测试：提交申请 → 审批人审批 → 结果通知 → 历史记录。

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 审批工作流模块问题修复"
```

---

### Task 18: 审查模块8 - 数据统计与分析

**Files:**
- Review: `backend/app/api/v1/data/analytics.py`
- Review: `backend/app/api/v1/data/statistics.py`
- Review: `frontend/src/views/analytics/`

- [ ] **Step 1: 检查统计接口的缓存覆盖情况**

```bash
grep -n "cache\|ttl\|TTL" "C:/military-Rural Revitalization-system/backend/app/api/v1/data/analytics.py" | head -20
```

- [ ] **Step 2: 检查图表数据边界情况**

空数据时图表组件是否正常显示（不报错）：
```bash
grep -n "v-if\|empty\|noData\|isEmpty" "C:/military-Rural Revitalization-system/frontend/src/views/analytics/dashboard/Dashboard.vue" | head -20
```

- [ ] **Step 3: 验证数据统计操作路径**

测试：各统计图表正常加载 → 过滤条件 → 导出数据。

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 数据统计分析模块问题修复"
```

---

### Task 19: 审查模块9 - 全局搜索

**Files:**
- Review: `backend/app/api/v1/search.py`
- Review: `frontend/src/components/GlobalSearch.vue`

- [ ] **Step 1: 检查搜索接口的防注入**

```bash
grep -n "like\|LIKE\|ilike\|%.*%" "C:/military-Rural Revitalization-system/backend/app/api/v1/search.py" | head -20
```

确认使用参数绑定而非字符串拼接：
```python
# 安全（使用参数绑定）
.filter(Model.name.ilike(f"%{keyword}%"))  # SQLAlchemy 会自动处理参数绑定

# 危险（字符串拼接 - 应避免）
.filter(text(f"name LIKE '%{keyword}%'"))
```

- [ ] **Step 2: 检查搜索防抖（前端）**

```bash
grep -n "debounce\|setTimeout\|delay" "C:/military-Rural Revitalization-system/frontend/src/components/GlobalSearch.vue" | head -10
```

确认搜索输入有防抖（至少300ms）。

- [ ] **Step 3: 验证全局搜索操作路径**

测试：Ctrl+K 打开 → 输入关键词 → 结果展示 → 点击跳转。

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 全局搜索模块问题修复"
```

---

### Task 20: 审查模块10 - 备份与同步

**Files:**
- Review: `backend/app/api/v1/system/backup.py`
- Review: `backend/app/services/backup_service.py`
- Review: `frontend/src/views/dataManagement/`

- [ ] **Step 1: 检查备份文件路径安全**

```bash
grep -n "get_app_data_dir\|get_backup_dir\|path\|Path(" "C:/military-Rural Revitalization-system/backend/app/services/backup_service.py" | head -20
```

确认使用 `paths.py` 的动态路径函数，不使用硬编码路径。

- [ ] **Step 2: 检查备份文件的访问权限控制**

确认只有管理员能下载/删除备份文件。

- [ ] **Step 3: 验证备份操作路径**

测试：创建备份 → 列表显示 → 下载 → 恢复（谨慎执行）。

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 备份与同步模块问题修复"
```

---

### Task 21: 审查模块11 - 系统设置

**Files:**
- Review: `backend/app/api/v1/system/system_config.py`
- Review: `backend/app/api/v1/system/admin.py`
- Review: `frontend/src/views/system/`

- [ ] **Step 1: 检查系统配置更新的权限**

```bash
grep -n "admin\|superuser\|is_admin\|require_admin" "C:/military-Rural Revitalization-system/backend/app/api/v1/system/admin.py" | head -20
```

- [ ] **Step 2: 检查敏感配置字段是否在响应中被过滤**

密码、密钥等字段不应出现在 GET 响应中。

- [ ] **Step 3: 验证系统设置操作路径**

测试：查看配置 → 修改配置 → 保存生效。

- [ ] **Step 4: 修复发现的 P1/P2 问题，Commit**

```bash
git commit -m "fix: 系统设置模块问题修复"
```

---

### Task 22: 审查模块12 - 离线地图

**Files:**
- Review: `backend/app/services/offline_map_service.py`
- Review: `frontend/src/components/map/OfflineMap.vue`

- [ ] **Step 1: 检查地图文件路径使用动态路径**

```bash
grep -n "get_data_path\|map_tiles\|Path(" "C:/military-Rural Revitalization-system/backend/app/services/offline_map_service.py" | head -10
```

确认使用 `get_data_path("map_tiles")` 而非硬编码路径。

- [ ] **Step 2: 检查地图瓦片请求的错误处理**

地图瓦片不存在时应返回 404 而非 500。

- [ ] **Step 3: 检查前端地图组件离线降级**

地图服务不可用时的降级处理。

- [ ] **Step 4: Commit**

```bash
git commit -m "fix: 离线地图模块问题修复"
```

---

## 阶段完成验证

### 阶段一验证

- [ ] 启动后端服务，检查路由加载数量（应为637条）

- [ ] 触发 404 错误，验证响应格式为 `{ code, message, errors?, meta }`：
```bash
curl -s http://localhost:8000/api/v1/nonexistent | python -m json.tool
# 预期：{ "code": 404, "message": "...", "meta": {...} }
# 不应出现：{ "success": false, "error": "...", "path": "..." }
```

- [ ] 触发验证错误（422），验证字段级错误格式：
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool
# 预期：{ "code": 422, "message": "请求参数验证失败", "errors": [...] }
```

- [ ] 前端登录后触发不存在路由，确认显示中文友好提示（不显示原始 JSON 或 "undefined"）

### 阶段二验证

```bash
# 检查索引创建日志
python -c "
from app.core.database import engine
from app.core.database_indexes import create_indexes
create_indexes(engine)
"
```

### 阶段三验证

- [ ] 项目列表页有 loading 状态
- [ ] 新建项目保存后列表自动刷新
- [ ] 编辑弹窗关闭后表单重置

### 最终验收

- [ ] 后端日志无 500 错误
- [ ] 浏览器 console 无 `TypeError`/`undefined` 报错
- [ ] 12个模块的核心操作路径人工验证全部通过
