# 设计规范：代码审查缺陷修复

**日期**: 2026-06-19
**状态**: 已设计，待实施（v2 — 经规范审查）
**范围**: 后端 RBAC 服务/API + 前端权限组件 + 前端 treeNormalizer 工具

---

## 背景

全面的代码审查发现了 6 个缺陷，分为三个层面：

1. **数据完整性** — 批量 grant/revoke 端点缺少事务原子性
2. **前端防御性** — 权限加载静默失败 + 响应忽视
3. **工具健壮性** — ID 规范化中的 treeNormalizer 边界情况

---

## 第 1 部分：数据完整性 — 批量操作的原子事务

### 缺陷

- `grant_permission` 端点（`rbac.py:335`）循环调用 `rbac_service.grant_permission()`，后者执行独立的 `db.commit()`。一次失败会使数据库处于永久不一致状态。
- `revoke_permission` 端点（`rbac.py:356`）同样循环调用 `rbac_service.revoke_permissions_batch()`，后者调用 `revoke_permission()`，各自执行 `db.commit()`。
- `revoke_permissions_batch`（`rbac_service.py:432`）为 N 个权限执行 N 次独立的 `DELETE` + `COMMIT` 往返，而单条 `DELETE ... WHERE permission IN (...)` 查询即可完成。

### 设计

#### 事务策略：采用现有 `transaction.py` 框架

项目已在 `backend/app/core/transaction.py` 中内置了完整的事务管理基础设施：
- `TransactionManager.transaction(db)` — 上下文管理器，自动在成功时提交、异常时回滚
- `TransactionManager.run_in_transaction(func, db, ...)` — 函数包装器，提交/回滚
- `BatchOperation.batch_delete(db, model_class, ids)` — 批量删除，flush-then-commit 模式

**采用此框架**，而非手动添加 try/commit/rollback 代码块。

#### Commit/flush 所有权策略

| 方法类型 | 策略 | 理由 |
|----------|------|------|
| 单操作服务方法（`assign_role`, `revoke_role`） | 保留 `db.commit()` | 被具有不同事务需求的多个调用方使用；每个调用为一个原子单元 |
| 循环/批量服务方法（`grant_permission`, `revoke_permissions_batch`） | 改用 `db.flush()` | 调用方（API 路由）通过 `transaction.py` 上下文管理器拥有事务边界 |

此策略在 `rbac_service.py` 顶部以注释形式记录。

#### 服务层（`backend/app/services/rbac_service.py`）

1. **`grant_permission()`**：将 `db.commit()` 替换为 `db.flush()`。

2. **`revoke_permissions_batch()`**：替换为单个批量 DELETE + 预查询失败重建：

```python
async def revoke_permissions_batch(
    self, user_id: str, permissions: List[str], db: Session = None
) -> tuple:
    """批量撤销用户权限。返回 (revoked: List[str], failed: List[str])。
    
    使用预查询方式确定哪些权限实际存在：
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
    
    revoked = list(existing)
    failed = missing
    return revoked, failed
```

预查询方式避免了 TOCTOU 竞态（在事务内运行，由 API 路由管理提交），并提供精确的 revoked/failed 拆分。

#### API 路由（`backend/app/api/v1/auth/rbac.py`）

3. **`grant_permission` 端点**：使用 `TransactionManager.transaction(db)` 包裹循环。无需嵌套函数——直接将循环放入 `with` 代码块（变量 `granted`/`failed` 可从封闭的 `async def` 函数作用域访问和修改）：

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

4. **`revoke_permission` 端点**：相同的事务包裹模式，使用 `TransactionManager.transaction(db)`：

```python
@router.post("/revoke/permission")
async def revoke_permission(revoke: PermissionGrant, db: Session = Depends(get_db), ...):
    with TransactionManager.transaction(db) as sess:
        revoked, failed = await rbac_service.revoke_permissions_batch(
            user_id=str(revoke.user_id), permissions=revoke.permissions, db=sess)
    return {"success": len(failed) == 0, "revoked": revoked, "failed": failed, ...}
```

### 调用方影响

- Grep 确认只有 `rbac.py` 中的 API 路由调用 `grant_permission()` 和 `revoke_permissions_batch()`。无其他调用方需要 `db.commit()` 变更。
- 单操作服务方法（`assign_role`, `revoke_role`）不变 — 保留自身 `db.commit()`。
- `TransactionManager.transaction(db)` 上下文管理器在异常时自动回滚，解决了端点原先缺失显式回滚的问题。

---

## 第 2 部分：前端防御性修复

### 缺陷

- **`loadCurrentPermissions`**（`PermissionAssignmentDrawer.vue:180`）：catch 处理程序静默重置 `currentPermissions = []`。结合新的 revoke-then-grant 保存流程，加载失败后保存会撤销所有现有权限。
- **`savePermissions`**（`PermissionAssignmentDrawer.vue:234`）：检查 `res.data?.failed` 但跳过 `res.data?.success`，可能将部分失败报告为成功。

### 设计

`PermissionAssignmentDrawer.vue` 中的四处变更：

1. **新增状态**：`const permissionsLoadFailed = ref(false)`

2. **加载处理增强**：
   - 成功：`currentPermissions = perms`，`permissionsLoadFailed = false`
   - 失败：`permissionsLoadFailed = true`，`currentPermissions = null`（保留之前的值，不覆写）

3. **模板横幅**（权限树上方）：
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

4. **保存按钮**：`:disabled="permissionsLoadFailed || savingPermissions"`

5. **保存响应检查**：检查 `res.data?.success` 和 `res.data?.failed`；若任一指示失败则显示 `ElMessage.warning`。仅当两个响应都返回 `success: true` 且没有失败项时，才显示 `ElMessage.success`。

---

## 第 3 部分：treeNormalizer 工具加固

### 缺陷

- **`normalizeTreeNodes`**（`treeNormalizer.ts:27`）：`String(node.id ?? node.key ?? "")` 在两个字段均为 null/undefined 时产生空字符串。多个节点共享键 `""` 会破坏 el-tree-select 节点标识。
- **`normalizeTreeNode`**（`treeNormalizer.ts:14`）：`...node` 展开传递所有原始 API 属性，包括带有未标准化数值型 id 的嵌套子节点——深层级仍存在原始 DOM 错误的风险。

### 设计

`treeNormalizer.ts` 中的两处变更：

1. **`normalizeTreeNodes`**：将空字符串回退替换为稳定的、基于内容的回退键：
   ```typescript
   // 之前：id: String(node.id ?? node.key ?? "")
   // 之后：稳定回退确保跨次重新标准化的键一致
   id: String(node.id ?? node.key ?? `_node_${node.name ?? ''}_${node.label ?? ''}`)
   ```

   `_node_` 前缀确保键以字母开头（XML Name 要求）。基于内容的回退意味着同一节点数据在重新渲染时获得相同键，避免 Vue 虚拟 DOM 抖动。**理由**：此回退路径永远不应被格式良好的后端数据命中；存在仅用于防御 DOM 崩溃，而非优化重新渲染。基于内容比 `crypto.randomUUID()` 更受欢迎，因为它是确定性的、可调试的，并且足够应对此防御性场景。

2. **`normalizeTreeNode`**：将 `...node` 展开替换为显式属性白名单 + 递归子节点标准化：
   ```typescript
   export function normalizeTreeNode(node: any): any {
     const children = node.children?.length ? normalizeTreeNodes(node.children) : undefined
     return {
       id: String(node.id ?? node.key ?? `_node_${node.name ?? ''}_${node.label ?? ''}`),
       name: node.name,
       label: node.label ?? node.name,
       children,
       leaf: children ? children.length === 0 : (node.leaf ?? !node.children?.length),
     }
   }
   ```

   白名单确保仅将已知安全属性传递给 Element Plus 树组件。API 元数据（如 `code`、`parent_id`、`sort_order`、`contact_person` 等）被过滤掉。

3. **`UserPermissions.vue`**：将 `normalizeTreeNode`（单节点，非递归）替换为 `normalizeTreeNodes`（递归），确保所有嵌套层级均被覆盖。对于延迟加载的树，`loadNode` 回调已按级别调用；递归标准化作为深度嵌套 API 响应的防御措施。

---

## 测试计划

| 层级 | 测试内容 |
|------|---------|
| 后端单元测试 | `grant_permission` 循环通过 `TransactionManager.transaction` 回滚；`revoke_permissions_batch` 预查询返回正确的 revoked/failed 拆分 |
| 后端单元测试 | 3 次 success `flush()` + 1 次 failure 后被 `rollback()` 正确撤销（核心原子性保证） |
| 后端单元测试 | `revoke_permissions_batch` 将从未存在的权限报告为 `failed`，而非 `revoked` |
| 后端集成测试 | HTTP 200 + `success: false` + `failed: [...]` 在 partial-revoke 后不产生残留数据 |
| 前端单元测试 | `normalizeTreeNodes` 为 null-id 节点生成稳定的 `_node_name_label` 键 |
| 前端单元测试 | `normalizeTreeNode` 输出仅包含白名单键（`id`、`name`、`label`、`children`、`leaf`） |
| 前端单元测试 | `savePermissions` 在 `permissionsLoadFailed === true` 时为 no-op |
| 前端 E2E | 权限加载失败 → 横幅显示 → 保存按钮禁用；保存后部分失败 → 警告 toast |

---

## 实施顺序

1. 后端 `rbac_service.py` — grant_permission 的 flush 变更 + revoke_permissions_batch 的预查询重构
2. 后端 `rbac.py` — 通过 `TransactionManager.transaction()` 进行事务包裹（grant + revoke 端点）
3. 前端 `treeNormalizer.ts` — 稳定回退键 + 白名单属性 + 递归子节点
4. 前端 `PermissionAssignmentDrawer.vue` — `permissionsLoadFailed` 状态 + 横幅 + 按钮禁用 + 响应检查
5. 前端 `UserPermissions.vue` — 切换到递归标准化
6. 运行完整测试套件（后端 7314 + 前端 1696）
