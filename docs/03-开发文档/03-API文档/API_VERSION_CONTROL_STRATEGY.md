# API版本控制策略

**日期**: 2026-03-13
**系统**: 帮扶管理信息系统 v1.0.3
**当前API版本**: v1

---

## 目录

1. [当前状态](#当前状态)
2. [版本控制原则](#版本控制原则)
3. [版本升级策略](#版本升级策略)
4. [兼容性管理](#兼容性管理)
5. [实施计划](#实施计划)
6. [最佳实践](#最佳实践)

---

## 当前状态

### API结构

```
backend/app/api/
├── v1/                    # 当前版本（v1）
│   ├── __init__.py       # 路由聚合
│   ├── auth/             # 认证模块
│   ├── system/           # 系统模块
│   ├── import_export/    # 导入导出
│   ├── data/             # 数据分析
│   ├── villages.py       # 村庄管理
│   ├── funds.py          # 经费管理
│   ├── projects.py       # 项目管理
│   └── ... (68个路由文件)
└── (未来) v2/            # 下一版本
```

### 路由前缀

```python
# backend/app/api/v1/__init__.py
api_v1_router = APIRouter(prefix="/api/v1")

# 所有API端点格式
# GET  /api/v1/villages
# POST /api/v1/funds
# GET  /api/v1/system/health
```

### 前端API配置

```typescript
// frontend/src/api/request.ts
const request = axios.create({
  baseURL: '/api/v1',  // 硬编码v1版本
  timeout: 30000,
});
```

---

## 版本控制原则

### 1. 语义化版本

采用 **主版本.次版本.修订版本** 格式：

- **主版本（Major）**: 不兼容的API变更
  - 示例: v1 → v2
  - 触发条件: 删除端点、修改响应结构、更改认证方式

- **次版本（Minor）**: 向后兼容的功能新增
  - 示例: v1.1, v1.2
  - 触发条件: 新增端点、新增可选字段

- **修订版本（Patch）**: 向后兼容的问题修复
  - 示例: v1.0.1, v1.0.2
  - 触发条件: Bug修复、性能优化

### 2. URL版本控制

**推荐方式**: 在URL路径中包含版本号

```
✅ 推荐: /api/v1/villages
✅ 推荐: /api/v2/villages
❌ 不推荐: /api/villages?version=1
❌ 不推荐: Header: API-Version: 1
```

**优点**:
- 清晰直观
- 易于缓存
- 便于测试
- 支持浏览器直接访问

### 3. 版本生命周期

```
v1.0 ────────────────────────────────────────────────────
     │                                                    │
     │ 活跃开发期（6-12个月）                              │
     │                                                    │
     └─→ v2.0 发布 ──────────────────────────────────────
         │                                               │
         │ v1维护期（6个月）                              │
         │ - 仅修复严重bug                                │
         │ - 不添加新功能                                 │
         │                                               │
         └─→ v1弃用期（3个月）                           │
             │ - 发出弃用警告                             │
             │ - 引导用户迁移                             │
             │                                           │
             └─→ v1下线                                  │
                 - 停止支持                              │
                 - 返回410 Gone                          │
```

---

## 版本升级策略

### 何时创建新版本

#### 创建v2的触发条件

**必须创建新版本（Breaking Changes）**:

1. **删除API端点**
   ```python
   # v1: 存在
   DELETE /api/v1/villages/{id}

   # v2: 删除（改为软删除）
   # 端点不存在
   ```

2. **修改响应结构**
   ```python
   # v1响应
   {
     "id": 1,
     "name": "张村",
     "population": 1000
   }

   # v2响应（不兼容）
   {
     "village_id": 1,  # 字段名变更
     "village_name": "张村",
     "demographics": {  # 结构变更
       "population": 1000
     }
   }
   ```

3. **更改认证方式**
   ```python
   # v1: JWT Token
   Authorization: Bearer <token>

   # v2: OAuth 2.0
   Authorization: OAuth <token>
   ```

4. **修改请求参数**
   ```python
   # v1
   POST /api/v1/villages
   {
     "name": "张村",
     "code": "V001"  # 必填
   }

   # v2
   POST /api/v2/villages
   {
     "name": "张村",
     "code": "V001",
     "region_code": "R001"  # 新增必填字段
   }
   ```

**可以在当前版本实现（Non-Breaking Changes）**:

1. **新增API端点**
   ```python
   # v1中新增
   GET /api/v1/villages/{id}/statistics
   ```

2. **新增可选字段**
   ```python
   # v1响应（向后兼容）
   {
     "id": 1,
     "name": "张村",
     "population": 1000,
     "gdp": 5000000  # 新增可选字段
   }
   ```

3. **新增可选参数**
   ```python
   # v1（向后兼容）
   GET /api/v1/villages?page=1&page_size=20&sort_by=name  # 新增sort_by
   ```

---

## 兼容性管理

### 1. 版本共存

**目录结构**:

```
backend/app/api/
├── v1/
│   ├── __init__.py
│   ├── villages.py
│   └── funds.py
├── v2/
│   ├── __init__.py
│   ├── villages.py      # 新版本实现
│   └── funds.py         # 新版本实现
└── common/              # 共享代码
    ├── models.py
    ├── schemas.py
    └── utils.py
```

**路由注册**:

```python
# backend/app/main.py
from app.api.v1 import api_v1_router
from app.api.v2 import api_v2_router

app.include_router(api_v1_router)  # /api/v1/*
app.include_router(api_v2_router)  # /api/v2/*
```

### 2. 代码复用

**共享业务逻辑**:

```python
# app/api/common/village_service.py
class VillageService:
    @staticmethod
    def get_village(db: Session, village_id: int):
        return db.query(Village).filter(Village.id == village_id).first()

# app/api/v1/villages.py
from app.api.common.village_service import VillageService

@router.get("/{village_id}")
def get_village_v1(village_id: int, db: Session = Depends(get_db)):
    village = VillageService.get_village(db, village_id)
    return VillageResponseV1.from_orm(village)

# app/api/v2/villages.py
from app.api.common.village_service import VillageService

@router.get("/{village_id}")
def get_village_v2(village_id: int, db: Session = Depends(get_db)):
    village = VillageService.get_village(db, village_id)
    return VillageResponseV2.from_orm(village)  # 不同的响应模型
```

### 3. 弃用警告

**响应头标记**:

```python
# app/api/v1/villages.py
from fastapi import Response

@router.get("/{village_id}")
def get_village(village_id: int, response: Response, db: Session = Depends(get_db)):
    # 添加弃用警告头
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Sunset"] = "2026-12-31"  # 下线日期
    response.headers["X-API-Upgrade-To"] = "/api/v2/villages"

    village = db.query(Village).filter(Village.id == village_id).first()
    return village
```

**响应体警告**:

```python
{
  "data": {...},
  "meta": {
    "deprecated": true,
    "sunset_date": "2026-12-31",
    "upgrade_to": "/api/v2/villages",
    "message": "此API将于2026-12-31下线，请迁移到v2版本"
  }
}
```

### 4. 版本检测中间件

```python
# app/middleware/api_version.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class APIVersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 检测API版本
        if request.url.path.startswith("/api/v1"):
            # 添加版本信息到响应头
            response = await call_next(request)
            response.headers["X-API-Version"] = "1.0.3"
            response.headers["X-API-Latest-Version"] = "2.0.0"
            return response

        return await call_next(request)

# app/main.py
app.add_middleware(APIVersionMiddleware)
```

---

## 实施计划

### 阶段1: 准备期（1-2周）

**目标**: 建立版本控制基础设施

1. **创建版本管理文档**
   - ✅ 本文档
   - API变更日志模板
   - 迁移指南模板

2. **添加版本检测中间件**
   ```python
   # 实现APIVersionMiddleware
   # 添加版本信息到响应头
   ```

3. **前端API版本配置**
   ```typescript
   // 支持动态切换API版本
   const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';
   const baseURL = `/api/${API_VERSION}`;
   ```

### 阶段2: v1稳定期（当前）

**目标**: 保持v1稳定，收集改进需求

1. **记录Breaking Changes需求**
   - 创建 `API_CHANGES.md` 文档
   - 记录所有不兼容变更需求

2. **实施Non-Breaking Changes**
   - 新增端点
   - 新增可选字段
   - 性能优化

3. **监控API使用情况**
   - 记录各端点调用频率
   - 识别高频API
   - 发现性能瓶颈

### 阶段3: v2规划期（未来3-6个月）

**目标**: 设计v2 API

1. **需求整理**
   - 汇总Breaking Changes
   - 设计新的API结构
   - 编写v2 API规范

2. **原型开发**
   - 创建 `app/api/v2/` 目录
   - 实现核心API
   - 编写测试用例

3. **文档编写**
   - v2 API文档
   - v1→v2迁移指南
   - 变更对比表

### 阶段4: v2发布期（未来6-12个月）

**目标**: 平滑过渡到v2

1. **Beta测试**
   - 内部测试v2 API
   - 收集反馈
   - 修复问题

2. **正式发布**
   - 发布v2 API
   - 同时维护v1和v2
   - 发布迁移指南

3. **用户迁移**
   - 引导用户迁移到v2
   - 提供迁移工具
   - 技术支持

### 阶段5: v1下线期（未来12-18个月）

**目标**: 逐步下线v1

1. **弃用警告（3个月）**
   - 添加弃用警告头
   - 发送通知邮件
   - 更新文档

2. **只读模式（2个月）**
   - v1仅支持GET请求
   - POST/PUT/DELETE返回410
   - 强制迁移到v2

3. **完全下线**
   - 移除v1代码
   - 返回410 Gone
   - 重定向到v2

---

## 最佳实践

### 1. API设计原则

**RESTful规范**:
```
GET    /api/v1/villages          # 列表
GET    /api/v1/villages/{id}     # 详情
POST   /api/v1/villages          # 创建
PUT    /api/v1/villages/{id}     # 更新
DELETE /api/v1/villages/{id}     # 删除
```

**响应格式统一**:
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "meta": {
    "version": "1.0.3",
    "timestamp": "2026-03-13T10:00:00Z"
  }
}
```

### 2. 文档管理

**API文档**:
- 使用FastAPI自动生成文档
- 访问: `/docs` (Swagger UI)
- 访问: `/redoc` (ReDoc)

**变更日志**:
```markdown
# API变更日志

## v1.0.3 (2026-03-13)
### 新增
- 新增唯一性验证API: `/api/v1/validation/check-unique`

### 修复
- 修复备份API路径不匹配问题

## v1.0.2 (2026-03-10)
### 优化
- 优化数据库连接池配置
```

### 3. 测试策略

**版本兼容性测试**:
```python
# tests/api/test_version_compatibility.py
def test_v1_response_structure():
    """确保v1响应结构不变"""
    response = client.get("/api/v1/villages/1")
    assert "id" in response.json()
    assert "name" in response.json()
    assert "code" in response.json()

def test_v2_new_fields():
    """测试v2新增字段"""
    response = client.get("/api/v2/villages/1")
    assert "region_code" in response.json()
```

### 4. 监控告警

**版本使用统计**:
```python
# 记录各版本API调用量
metrics = {
    "v1_requests": 1000,
    "v2_requests": 50,
    "v1_deprecated_endpoints": 10
}
```

**告警规则**:
- v1调用量 >90%: 提醒用户迁移
- v1弃用端点调用: 发送通知
- v2错误率 >5%: 紧急修复

---

## 附录

### A. API变更检查清单

**发布前检查**:

- [ ] 是否有Breaking Changes？
  - [ ] 删除端点
  - [ ] 修改响应结构
  - [ ] 更改认证方式
  - [ ] 修改必填参数

- [ ] 是否需要创建新版本？
  - [ ] 是 → 创建v2
  - [ ] 否 → 在v1中实现

- [ ] 文档是否更新？
  - [ ] API文档
  - [ ] 变更日志
  - [ ] 迁移指南

- [ ] 测试是否通过？
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] 兼容性测试

### B. 版本迁移模板

```markdown
# v1 → v2 迁移指南

## 变更概述
- 响应结构优化
- 新增区域编码字段
- 删除已弃用端点

## 详细变更

### 1. 村庄API

#### 获取村庄详情
**v1**:
```
GET /api/v1/villages/{id}
Response: {
  "id": 1,
  "name": "张村",
  "code": "V001"
}
```

**v2**:
```
GET /api/v2/villages/{id}
Response: {
  "village_id": 1,
  "village_name": "张村",
  "village_code": "V001",
  "region_code": "R001"  # 新增
}
```

## 迁移步骤
1. 更新前端baseURL: `/api/v1` → `/api/v2`
2. 更新响应字段映射
3. 测试所有功能
4. 部署上线
```

### C. 参考资源

- [RESTful API设计指南](https://restfulapi.net/)
- [语义化版本规范](https://semver.org/lang/zh-CN/)
- [FastAPI版本控制](https://fastapi.tiangolo.com/advanced/sub-applications/)

---

## 总结

### 当前建议

**短期（0-6个月）**:
1. ✅ 保持v1稳定
2. ✅ 记录改进需求
3. ✅ 实施Non-Breaking Changes
4. ✅ 建立版本管理流程

**中期（6-12个月）**:
1. 评估是否需要v2
2. 如需要，开始v2设计
3. 实施Beta测试
4. 准备迁移文档

**长期（12-18个月）**:
1. 发布v2（如需要）
2. 维护v1和v2共存
3. 引导用户迁移
4. 逐步下线v1

### 评分

**API版本控制策略**: ⭐⭐⭐⭐⭐ (5.0/5)

- ✅ 清晰的版本控制原则
- ✅ 完整的升级策略
- ✅ 详细的实施计划
- ✅ 最佳实践指南

---

**文档版本**: 1.0
**最后更新**: 2026-03-13
**维护人员**: 系统架构团队
