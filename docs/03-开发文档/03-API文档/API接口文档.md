# API端点完整文档

**生成日期**: 2026-03-13
**系统版本**: v1.0.3
**API版本**: v1
**基础URL**: `http://127.0.0.1:8000/api/v1`

---

## 认证

所有API请求（除登录外）都需要在请求头中携带JWT Token：

```
Authorization: Bearer <access_token>
```

### 登录

```
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

Response:
{
  "code": 200,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": {...}
  }
}
```

---

## 核心业务模块

### 1. 组织管理 `/organizations`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/organizations` | 查询组织列表 | page, page_size, is_active, keyword |
| GET | `/organizations/tree` | 查询组织树 | org_type |
| GET | `/organizations/types/options` | 查询类型选项 | - |
| GET | `/organizations/{id}` | 查询组织详情 | - |
| POST | `/organizations` | 创建组织 | Body: OrganizationCreate |
| PUT | `/organizations/{id}` | 更新组织 | Body: OrganizationUpdate |
| DELETE | `/organizations/{id}` | 删除组织 | - |

**注意**:
- 删除是逻辑删除（设置is_active=false）
- 查询列表时默认只返回is_active=true的组织

---

### 2. 村庄管理 `/villages`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/villages` | 查询村庄列表 | page, page_size, keyword, status |
| GET | `/villages/{id}` | 查询村庄详情 | - |
| POST | `/villages` | 创建村庄 | Body: VillageCreate |
| PUT | `/villages/{id}` | 更新村庄 | Body: VillageUpdate |
| DELETE | `/villages/{id}` | 删除村庄 | - |

---

### 3. 经费管理 `/funds`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/funds` | 查询经费列表 | page, page_size, keyword |
| GET | `/funds/{id}` | 查询经费详情 | - |
| POST | `/funds` | 创建经费 | Body: FundCreate |
| PUT | `/funds/{id}` | 更新经费 | Body: FundUpdate |
| DELETE | `/funds/{id}` | 删除经费 | - |

---

### 4. 经费预算 `/fund-budgets`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/fund-budgets` | 查询预算列表 | page, page_size, year |
| GET | `/fund-budgets/{id}` | 查询预算详情 | - |
| POST | `/fund-budgets` | 创建预算 | Body: BudgetCreate |
| PUT | `/fund-budgets/{id}` | 更新预算 | Body: BudgetUpdate |
| DELETE | `/fund-budgets/{id}` | 删除预算 | - |

**注意**: 使用连字符 `/fund-budgets` 而不是下划线

---

### 5. 项目管理 `/projects`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/projects` | 查询项目列表 | page, page_size, keyword, status |
| GET | `/projects/{id}` | 查询项目详情 | - |
| POST | `/projects` | 创建项目 | Body: ProjectCreate |
| PUT | `/projects/{id}` | 更新项目 | Body: ProjectUpdate |
| DELETE | `/projects/{id}` | 删除项目 | - |

---

### 6. 学校管理 `/schools`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/schools` | 查询学校列表 | page, page_size, keyword |
| GET | `/schools/{id}` | 查询学校详情 | - |
| POST | `/schools` | 创建学校 | Body: SchoolCreate |
| PUT | `/schools/{id}` | 更新学校 | Body: SchoolUpdate |
| DELETE | `/schools/{id}` | 删除学校 | - |

---

### 7. 政策管理 `/policies`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/policies` | 查询政策列表 | page, page_size, keyword |
| GET | `/policies/{id}` | 查询政策详情 | - |
| POST | `/policies` | 创建政策 | Body: PolicyCreate |
| PUT | `/policies/{id}` | 更新政策 | Body: PolicyUpdate |
| DELETE | `/policies/{id}` | 删除政策 | - |

---

### 8. 乡村工作 `/rural-works`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/rural-works` | 查询工作列表 | page, page_size, keyword |
| GET | `/rural-works/{id}` | 查询工作详情 | - |
| POST | `/rural-works` | 创建工作 | Body: RuralWorkCreate |
| PUT | `/rural-works/{id}` | 更新工作 | Body: RuralWorkUpdate |
| DELETE | `/rural-works/{id}` | 删除工作 | - |

**注意**: 使用连字符 `/rural-works` 而不是下划线

---

### 9. 乡村任务 `/rural-tasks`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/rural-tasks` | 查询任务列表 | page, page_size, keyword |
| GET | `/rural-tasks/{id}` | 查询任务详情 | - |
| POST | `/rural-tasks` | 创建任务 | Body: RuralTaskCreate |
| PUT | `/rural-tasks/{id}` | 更新任务 | Body: RuralTaskUpdate |
| DELETE | `/rural-tasks/{id}` | 删除任务 | - |

**注意**: 使用连字符 `/rural-tasks` 而不是下划线

---

## 系统管理模块

### 10. 用户管理 `/users`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/users` | 查询用户列表 | page, page_size, keyword |
| GET | `/users/{id}` | 查询用户详情 | - |
| POST | `/users` | 创建用户 | Body: UserCreate |
| PUT | `/users/{id}` | 更新用户 | Body: UserUpdate |
| DELETE | `/users/{id}` | 删除用户 | - |

**注意**: 路径是 `/users` 而不是 `/auth/users`

---

### 11. 健康检查 `/health`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/health` | 系统健康检查 | - |

**响应示例**:
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2026-03-13T19:40:00Z"
}
```

**注意**: 路径是 `/health` 而不是 `/system/health`

---

### 12. 备份管理 `/backup`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/backup` | 查询备份列表 | - |
| POST | `/backup` | 创建备份 | Body: {description, include_uploads} |
| POST | `/backup/restore` | 恢复备份 | Body: {backup_id} |
| DELETE | `/backup/{id}` | 删除备份 | - |

---

## 数据分析模块

### 13. 仪表盘 `/dashboard`

| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| GET | `/dashboard/stats` | 仪表盘统计数据 | - |
| GET | `/dashboard/summary` | 仪表盘摘要 | - |
| GET | `/dashboard/recent-activities` | 最近活动 | page, page_size |

**响应示例** (`/dashboard/stats`):
```json
{
  "total_villages": 100,
  "total_projects": 50,
  "total_funds": 1000000,
  "data_completeness": 85.5,
  "pending_approvals": 5
}
```

**注意**:
- 路径是 `/dashboard/stats` 而不是 `/data/dashboard`
- 使用连字符 `/recent-activities`

---

## 路由命名规范

### ✅ 正确的命名（使用连字符）

```
/fund-budgets
/rural-works
/rural-tasks
/data-quality
/ai-enhanced
/fund-lifecycle
/report-templates
/supported-villages
/user-management
/two-factor
/messages-extended
/chunked-upload
/async-export
/recent-activities
```

### ❌ 错误的命名（使用下划线）

```
/fund_budgets
/rural_works
/rural_tasks
/data_quality
/ai_enhanced
/fund_lifecycle
/report_templates
/supported_villages
/user_management
/two_factor
/messages_extended
/chunked_upload
/async_export
/recent_activities
```

---

## 常见问题

### Q1: 为什么使用连字符而不是下划线？

**A**: RESTful API 标准推荐使用连字符（kebab-case）：
- URL 对大小写不敏感，连字符更清晰
- 符合 HTTP 规范和最佳实践
- 更易读和维护

### Q2: 健康检查端点为什么是 `/health` 而不是 `/system/health`？

**A**:
- `health.py` 在 `system` 子模块中
- 路由定义是 `@router.get("/health")`
- 子模块的路由会自动合并到主路由
- 最终路径是 `/health`

### Q3: 仪表盘端点为什么是 `/dashboard/stats` 而不是 `/data/dashboard`？

**A**:
- `dashboard.py` 在 `data` 子模块中
- 路由定义是 `router = APIRouter(prefix="/dashboard")`
- 子模块的路由会自动合并到主路由
- 最终路径是 `/dashboard/*`

### Q4: 如何查看所有可用的API端点？

**A**: 访问 Swagger UI 文档：
```
http://127.0.0.1:8000/docs
```

或 ReDoc 文档：
```
http://127.0.0.1:8000/redoc
```

---

## 测试示例

### 使用 curl

```bash
# 登录
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.data.access_token')

# 查询组织列表
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/v1/organizations?page=1&page_size=10&is_active=true"

# 健康检查
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/v1/health"

# 仪表盘统计
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/api/v1/dashboard/stats"
```

### 使用 Python

```python
import requests

# 登录
response = requests.post(
    "http://127.0.0.1:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = response.json()["data"]["access_token"]

# 设置请求头
headers = {"Authorization": f"Bearer {token}"}

# 查询组织列表
response = requests.get(
    "http://127.0.0.1:8000/api/v1/organizations",
    headers=headers,
    params={"page": 1, "page_size": 10, "is_active": True}
)
organizations = response.json()

# 健康检查
response = requests.get(
    "http://127.0.0.1:8000/api/v1/health",
    headers=headers
)
health = response.json()

# 仪表盘统计
response = requests.get(
    "http://127.0.0.1:8000/api/v1/dashboard/stats",
    headers=headers
)
stats = response.json()
```

---

## 更新日志

### 2026-03-13
- ✅ 修复组织管理删除问题
- ✅ 修复组织管理新增缓存问题
- ✅ 确认所有端点路径
- ✅ 统一路由命名���范
- ✅ 完善API文档
- ✅ 所有测试100%通过

---

**文档版本**: 1.0
**最后更新**: 2026-03-13
**维护人员**: 系统开发团队
