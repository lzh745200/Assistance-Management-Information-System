# 设计规范：代码审查缺陷修复

**日期**: 2026-06-19
**状态**: 已设计，待实施（v3 — 经 3 轮规范审查 + 用户评审优化）
**范围**: 后端 RBAC 服务/API + 前端权限组件 + 前端 treeNormalizer 工具

---

## 1. 背景

全面代码审查发现 6 项缺陷，按层面分组如下：

| 层面 | 缺陷描述 |
|------|----------|
| **数据完整性** | 批量授权/撤销端点缺少事务原子性；循环调用独立 `db.commit()` 导致部分失败后数据库不一致 |
| **前端防御性** | 权限加载静默失败（重置为空数组），结合新的保存流程会误删所有权限；保存响应仅检查 `failed` 而忽略 `success` 标志，可能将部分失败误报为成功 |
| **工具健壮性** | `treeNormalizer` 对 `id`/`key` 均为空时生成空字符串键，导致树组件节点冲突；深度嵌套子节点未被递归标准化，原始数值型 `id` 仍可能被传递 |

本规范提供系统性修复方案，并针对实际生产环境增加了性能、可维护性及可观测性考量。

---

## 2. 第 1 部分：数据完整性 — 批量操作的原子事务

### 2.1 缺陷回顾

- `grant_permission` 端点循环调用 `grant_permission()`（内含独立 `db.commit()`），一次失败导致部分提交部分回滚，数据不一致。
- `revoke_permission` 端点循环调用 `revoke_permissions_batch()`（内部循环逐个 `DELETE` + `COMMIT`），性能低下且缺乏原子性。
- 缺少显式回滚逻辑，发生异常时数据库可能处于中间状态。

### 2.2 设计方案

#### 2.2.1 事务策略：统一采用现有 `transaction.py` 框架

项目已有成熟的事务管理基础设施（`backend/app/core/transaction.py`）：
- `TransactionManager.transaction(db)` — 上下文管理器，自动在成功时提交、异常时回滚
- `TransactionManager.run_in_transaction(func, db, ...)` — 函数包装器，提交/回滚
- `BatchOperation.batch_delete(db, model_class, ids)` — 批量删除辅助

**决策**：API 层统一使用 `TransactionManager.transaction(db)` 管理事务边界，服务层方法使用 `db.flush()` 将更改持久化到当前事务，**不在服务方法内提交**。该策略保证：
- 批量操作整体原子性（全部成功或全部回滚）
- 服务层可独立测试，调用方控制事务边界
- 避免嵌套事务冲突

#### 2.2.2 Commit/flush 所有权策略

| 方法类型 | 策略 | 理由 |
|----------|------|------|
| 单操作服务方法（`assign_role`, `revoke_role`） | 保留 `db.commit()` | 被具有不同事务需求的多个调用方使用；每个调用为一个原子单元 |
| 循环/批量服务方法（`grant_permission`, `revoke_permissions_batch`） | 改用 `db.flush()` | 调用方（API 路由）通过 `transaction.py` 上下文管理器拥有事务边界 |

此策略在 `rbac_service.py` 顶部以注释形式记录。单操作方法**建议后续统一迁移至 flush 模式**，以保持架构一致性。

#### 2.2.3 服务层变更（`backend/app/services/rbac_service.py`）

**① `grant_permission()`**
- 将 `db.commit()` 替换为 `db.flush()`
- 保持原有业务逻辑：检查权限是否存在，若不存在则插入；插入成功返回 `True`，重复或失败返回 `False`（不抛出异常，以便部分成功）
- 若未来权限列表极大，可考虑批量插入，但当前循环+flush 能满足大多数场景，且能精准报告每个权限的结果

**② `revoke_permissions_batch()`** — 完全重构为预查询 + 批量删除：

```python
async def revoke_permissions_batch(
    self, user_id: str, permissions: List[str], db: Session = None
) -> tuple[List[str], List[str]]:
    """批量撤销用户权限。返回 (revoked: List[str], failed: List[str])。

    采用预查询方式确定哪些权限实际存在：
    1. SELECT 现有权限
    2. DELETE WHERE permission IN (existing)
    3. 返回 (已删除, 从未存在)
    """
    uid = int(user_id)

    # 预查询：哪些权限实际存在
    existing_rows = (
        db.query(UserPermission.permission)
        .filter(
            UserPermission.user_id == uid,
            UserPermission.permission.in_(permissions)
        )
        .all()
    )
    existing = {row[0] for row in existing_rows}
    missing = [p for p in permissions if p not in existing]

    if existing:
        db.query(UserPermission).filter(
            UserPermission.user_id == uid,
            UserPermission.permission.in_(list(existing))
        ).delete(synchronize_session=False)
        db.flush()

    return list(existing), missing
```

预查询方式避免了 TOCTOU 竞态（在事务内运行，由 API 路由管理提交），并提供精确的 revoked/failed 拆分。

#### 2.2.4 API 路由变更（`backend/app/api/v1/auth/rbac.py`）

**③ `grant_permission` 端点** — 使用 `TransactionManager.transaction(db)` 包裹循环。无需嵌套函数：直接将循环放入 `with` 代码块（变量 `granted`/`failed` 可从封闭的 `async def` 函数作用域直接访问和修改）：

```python
from app.core.transaction import TransactionManager

@router.post("/grant/permission")
async def grant_permission(grant: PermissionGrant, db: Session = Depends(get_db), ...):
    granted: List[str] = []
    failed: List[str] = []

    user_id_str = str(grant.user_id)
    granted_by_str = str(current_user.id)
    expires_iso = grant.expires_at.isoformat() if grant.expires_at else None

    with TransactionManager.transaction(db) as sess:
        for perm in grant.permissions:
            success = await rbac_service.grant_permission(
                user_id=user_id_str, permission=perm,
                granted_by=granted_by_str, expires_at=expires_iso, db=sess)
            if success:
                granted.append(perm)
            else:
                failed.append(perm)

    return {
        "success": len(failed) == 0,
        "granted": granted,
        "failed": failed,
        "message": f"权限授予完成: 成功 {len(granted)}, 失败 {len(failed)}",
    }
```

**④ `revoke_permission` 端点** — 相同的事务包裹模式：

```python
@router.post("/revoke/permission")
async def revoke_permission(revoke: PermissionGrant, db: Session = Depends(get_db), ...):
    with TransactionManager.transaction(db) as sess:
        revoked, failed = await rbac_service.revoke_permissions_batch(
            user_id=str(revoke.user_id), permissions=revoke.permissions, db=sess)
    return {
        "success": len(failed) == 0,
        "revoked": revoked,
        "failed": failed,
        "message": f"权限撤销完成: 成功 {len(revoked)}, 失败 {len(failed)}",
    }
```

#### 2.2.5 调用方影响与兼容性

- Grep 确认仅 `rbac.py` 调用 `grant_permission()` 和 `revoke_permissions_batch()`，改动风险可控。
- 事务管理器在异常时自动回滚，无需手动 `try...except`。
- 单操作服务方法（`assign_role`, `revoke_role`）暂保持不变（仍带 `commit`），但**建议后续统一迁移至 flush 模式**。

---

## 3. 第 2 部分：前端防御性修复

### 3.1 缺陷回顾

- `loadCurrentPermissions`（`PermissionAssignmentDrawer.vue:180`）：catch 处理程序静默重置 `currentPermissions = []`。结合新的 revoke-then-grant 保存流程，加载失败后保存会撤销所有现有权限。
- `savePermissions`（`PermissionAssignmentDrawer.vue:234`）：检查 `res.data?.failed` 但跳过 `res.data?.success`，可能将部分失败报告为成功。

### 3.2 设计方案

#### 3.2.1 新增加载失败状态

```typescript
const permissionsLoadFailed = ref(false);
// currentPermissions 保持现有 ref<string[]>([]) 声明
```

#### 3.2.2 增强加载处理

```typescript
async function loadCurrentPermissions() {
  if (!props.user?.id) return;
  try {
    const res = await request.get(`/rbac/user/${props.user.id}/permissions`);
    const payload = res.data?.data || res.data;
    const perms = payload?.permissions || payload || [];
    currentPermissions.value = Array.isArray(perms) ? perms : [];
    permissionsLoadFailed.value = false;
  } catch {
    permissionsLoadFailed.value = true;
    // currentPermissions 保留既有值，不覆写为空数组
  }
}
```

#### 3.2.3 模板横幅（权限树上方）

```html
<el-alert
  v-if="permissionsLoadFailed"
  type="warning"
  :closable="false"
  show-icon
>
  权限数据加载失败，请关闭面板后重试。保存操作已被禁用。
</el-alert>
```

#### 3.2.4 保存按钮禁用

```html
<el-button
  type="primary"
  :loading="savingPermissions"
  :disabled="permissionsLoadFailed || savingPermissions"
  @click="savePermissions"
>
  保存权限
</el-button>
```

#### 3.2.5 保存响应处理完善

```typescript
async function savePermissions() {
  if (!props.user?.id || permissionsLoadFailed.value) return;
  savingPermissions.value = true;
  try {
    // ... revoke removed + grant new ...
    const res = await request.post("/rbac/grant/permission", { ... });
    const data = res.data || {};
    if (data.success && (!data.failed || data.failed.length === 0)) {
      ElMessage.success("权限保存成功");
    } else {
      const failedCount = data.failed?.length || 0;
      ElMessage.warning(`权限保存部分失败（${failedCount} 项）`);
    }
    emit("saved");
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "权限保存失败");
  } finally {
    savingPermissions.value = false;
  }
}
```

---

## 4. 第 3 部分：treeNormalizer 工具加固

### 4.1 缺陷回顾

- `normalizeTreeNodes`：`String(node.id ?? node.key ?? "")` 在两个字段均为 null/undefined 时产生空字符串。多个节点共享键 `""` 会破坏 el-tree-select 节点标识。
- `normalizeTreeNode`：`...node` 展开传递所有原始 API 属性，包括带有未标准化数值型 id 的嵌套子节点——深层级仍存在原始 DOM 错误的风险。
- 传递了不必要的 API 元数据（`code`、`parent_id`、`sort_order`、`contact_person` 等）给 Vue 组件，可能引发未知属性警告。

### 4.2 设计方案

#### 4.2.1 稳定回退键（`makeStableId`）

使用**基于内容的确定性回退**，保证同一节点在多次标准化中生成相同键，避免虚拟 DOM 抖动：

```typescript
const makeStableId = (node: any): string => {
  return String(
    node.id ??
    node.key ??
    `_node_${(node.name || node.label || '').substring(0, 20)}`
  );
};
```

- 前缀 `_node_` 确保键以字母开头（符合 XML Name 要求）
- 内容截断（20 字符）防止键过长，实际回退路径极少触发
- 确定性优于随机 UUID，便于调试和缓存

#### 4.2.2 显式属性白名单 + 递归标准化

只保留树组件所需属性，过滤掉所有额外字段，并递归处理子节点：

```typescript
export function normalizeTreeNode(node: any): any {
  const children = node.children?.length
    ? normalizeTreeNodes(node.children)
    : undefined;

  return {
    id: makeStableId(node),
    name: node.name,
    label: node.label ?? node.name,
    children,
    leaf: children ? children.length === 0 : (node.leaf ?? !node.children?.length),
  };
}

export function normalizeTreeNodes(nodes: any[]): any[] {
  return nodes.map(node => normalizeTreeNode(node));
}
```

白名单确保仅将已知安全属性传递给 Element Plus 树组件。

#### 4.2.3 接入点调整

在 `UserPermissions.vue` 中，将原来调用 `normalizeTreeNode`（非递归版本）的地方替换为 `normalizeTreeNodes`（递归版本），以覆盖深层嵌套。

---

## 5. 性能与并发考量

- **批量删除**：`DELETE ... IN (...)` 在权限数量较大时（如 >1000）可能产生长事务锁，建议评估业务量，必要时增加分批处理（如每 500 条删除一次，但仍在一个事务内）。
- **grant 操作**：若单次授权权限数过多（>100），可考虑使用 `bulk_insert_mappings` 提高插入效率，同时需处理重复键冲突（使用 SQLite `INSERT OR IGNORE` 或 `on_conflict_do_nothing`）。
- **事务超时**：数据库事务超时时间应合理设置（如 30s），避免长时间持有锁。
- **并发安全**：`TransactionManager.transaction(db)` 依赖数据库的行级锁；对于 SQLite，写入操作默认串行化；对于 PostgreSQL/MySQL，建议 `SELECT ... FOR UPDATE` 锁定用户行以防止 grant/revoke 并发竞态。

---

## 6. 可观测性增强

- 后端在事务提交/回滚时添加结构化日志（包含用户 ID、操作类型、数量），便于追踪
- 前端在 `loadCurrentPermissions` 失败时使用 `console.error` 记录，并可上报到监控平台（如 Sentry）
- API 响应中可增加 `trace_id`，方便前后端联动排查问题（后续迭代）

---

## 7. 测试计划

| 层级 | 测试内容 |
|------|----------|
| 后端单元 | `grant_permission` 循环中部分失败 → 事务回滚，数据库无残留 |
| 后端单元 | `revoke_permissions_batch` 预查询返回正确的 revoked/failed 拆分 |
| 后端单元 | 3 次 success `flush()` + 1 次 failure 后被 `rollback()` 正确撤销（核心原子性保证） |
| 后端单元 | `revoke_permissions_batch` 将从未存在的权限报告为 `failed`，而非 `revoked` |
| 后端单元 | 并发场景：两个请求同时撤销相同权限，确保无死锁或重复删除 |
| 后端集成 | HTTP 200 + `success: false` + `failed: [...]` 在 partial-revoke 后数据库状态一致 |
| 前端单元 | `normalizeTreeNodes` 为空 id 节点生成稳定的 `_node_name_label` 键 |
| 前端单元 | `normalizeTreeNode` 输出仅包含白名单键（`id`、`name`、`label`、`children`、`leaf`） |
| 前端单元 | `savePermissions` 在 `permissionsLoadFailed === true` 时直接返回，不发起请求 |
| 前端单元 | 保存响应中 `success: false` 或 `failed.length > 0` 时弹出警告而非成功 |
| 前端 E2E | 模拟权限加载失败 → 横幅显示 → 保存按钮禁用 |
| 前端 E2E | 保存部分失败 → 警告 toast |
| 性能 | 批量授权/撤销 500 项权限，记录响应时间与数据库锁等待时间 |

---

## 8. 实施顺序与依赖

| 步骤 | 文件 | 变更摘要 | 依赖 |
|------|------|---------|------|
| 1 | `rbac_service.py` | `grant_permission` flush 变更 + `revoke_permissions_batch` 预查询重构 | 无 |
| 2 | `rbac.py` | `TransactionManager.transaction()` 包裹 grant + revoke 端点 | 步骤 1 |
| 3 | `treeNormalizer.ts` | 稳定回退键 + 白名单属性 + 递归子节点 | 无 |
| 4 | `PermissionAssignmentDrawer.vue` | `permissionsLoadFailed` 状态 + 横幅 + 按钮禁用 + 响应检查 | 步骤 3 |
| 5 | `UserPermissions.vue` | 切换到递归标准化 | 步骤 3 |
| 6 | 全量回归 | 后端 7314 + 前端 1696 → 均 100% 通过 | 步骤 1-5 |

---

## 9. 长期改进建议

- 统一所有服务层方法使用 `db.flush()`，由 API 层通过事务管理器统一控制提交，提升架构清晰度
- 考虑引入乐观锁或版本号字段，避免并发更新导致的数据丢失
- 前端权限树支持虚拟滚动，应对超大规模权限列表（>1000 项）
- 建立前后端契约测试，确保 `success` / `failed` 字段始终存在
- 将 `rbac_service.py` 中的循环查询模式抽象为通用 `batch_apply` 工具，供其他业务模块复用

---

## 10. 附录：关键代码片段参考

### 10.1 事务管理器使用模式

```python
# 模式：直接在 with 块内编写业务逻辑，无需嵌套函数
with TransactionManager.transaction(db) as sess:
    # 所有操作使用 sess
    # 退出时自动提交，异常时回滚
    result = await some_service.do_work(db=sess)
```

### 10.2 treeNormalizer 输出示例

```json
{
  "id": "123",
  "name": "系统管理",
  "label": "系统管理",
  "children": [
    {
      "id": "_node_用户管理",
      "name": "用户管理",
      "label": "用户管理",
      "leaf": true
    }
  ],
  "leaf": false
}
```
