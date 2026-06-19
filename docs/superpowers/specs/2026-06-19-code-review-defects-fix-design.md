# 设计规范：代码审查缺陷修复

**日期**: 2026-06-19
**状态**: 已设计，待实施
**范围**: 后端 RBAC 服务/API + 前端权限组件 + 前端 treeNormalizer 工具

---

## 背景

全面的代码审查发现了 6 个缺陷，分为三个层面：

1. **数据完整性** — 批量 grant/revoke 端点缺少事务原子性
2. **前端防御性** — 权限加载静默失败 + 响应忽视
3. **工具健壮性** — ID 规范化中的 treeNormalizer 边界情况

本规范记录了每个层面的修复方案。

---

## 第 1 部分：数据完整性 — 批量操作的原子事务

### 缺陷

- `grant_permission` 端点（`rbac.py:335`）循环调用 `rbac_service.grant_permission()`，后者执行独立的 `db.commit()`。一次失败会使数据库处于永久不一致状态。
- `revoke_permission` 端点（`rbac.py:356`）同样循环调用 `rbac_service.revoke_permissions_batch()`，后者调用 `revoke_permission()`，各自执行 `db.commit()`。
- `revoke_permissions_batch`（`rbac_service.py:432`）为 N 个权限执行 N 次独立的 `DELETE` + `COMMIT` 往返，而单条 `DELETE ... WHERE permission IN (...)` 查询即可完成。

### 设计

#### 服务层（`backend/app/services/rbac_service.py`）

1. **`grant_permission()`**：将 `db.commit()` 替换为 `db.flush()`。调用方现在负责事务边界。
2. **`revoke_permissions_batch()`**：替换为单条批量 DELETE：

```python
async def revoke_permissions_batch(self, user_id: str, permissions: List[str], db: Session = None) -> tuple:
    rows = (
        db.query(UserPermission)
        .filter(
            UserPermission.user_id == int(user_id),
            UserPermission.permission.in_(permissions)
        )
        .delete(synchronize_session=False)
    )
    db.flush()  # 延迟提交，由调用方处理
    # 通过检查哪些权限仍然存在来重建 revoked/failed 列表
    ...
```

#### API 路由（`backend/app/api/v1/auth/rbac.py`）

3. **`grant_permission` 端点**：将循环包裹在显式事务中：

```python
try:
    for perm in grant.permissions:
        await rbac_service.grant_permission(...)
    db.commit()
except Exception:
    db.rollback()
    raise HTTPException(status_code=500, detail="批量授予失败 — 未应用任何更改")
```

4. **`revoke_permission` 端点**：相同的事务包裹模式。

### 调用方影响

Grep 确认只有 `rbac.py` 中的 API 路由调用 `grant_permission()`。无其他调用方需要 `db.commit()` 变更。

---

## 第 2 部分：前端防御性修复

### 缺陷

- **`loadCurrentPermissions`**（`PermissionAssignmentDrawer.vue:180`）：catch 处理程序静默重置 `currentPermissions = []`。结合新的 revoke-then-grant 保存流程，加载失败后保存会撤销所有现有权限。
- **`savePermissions`**（`PermissionAssignmentDrawer.vue:234`）：检查 `res.data?.failed` 但跳过 `res.data?.success`，可能将部分失败报告为成功。

### 设计

`PermissionAssignmentDrawer.vue` 中的三处变更：

1. **新增状态**：`const permissionsLoadFailed = ref(false)`

2. **加载处理增强**：
   - 成功：`currentPermissions = perms`，`permissionsLoadFailed = false`
   - 失败：`permissionsLoadFailed = true`，`currentPermissions = null`（不禁用树，但阻塞保存）

3. **保存按钮**：`:disabled="permissionsLoadFailed || savingPermissions"`

4. **保存响应检查**：同时检查 `res.data?.success` 和 `res.data?.failed`；两者任一指示失败均显示警告

5. **权限树上方模板横幅**：
```html
<el-alert v-if="permissionsLoadFailed" type="warning" :closable="false">
  权限加载失败 — 保存将覆盖此用户的现有权限
</el-alert>
```

---

## 第 3 部分：treeNormalizer 工具加固

### 缺陷

- **`normalizeTreeNodes`**（`treeNormalizer.ts:27`）：`String(node.id ?? node.key ?? "")` 在两个字段均为 null/undefined 时产生空字符串。多个节点共享键 `""` 会破坏 el-tree-select 节点标识。
- **`normalizeTreeNode`**（`treeNormalizer.ts:14`）：`...node` 展开传递所有原始 API 属性，包括带有未标准化数值型 id 的嵌套子节点——深层级仍存在原始 DOM 错误的风险。

### 设计

`treeNormalizer.ts` 中的两处变更：

1. **`normalizeTreeNodes`**：将最终回退替换为唯一键：
   ```typescript
   id: String(node.id ?? node.key ?? crypto.randomUUID())
   ```

2. **`normalizeTreeNode`**：替换 `...node` 展开为显式属性白名单 + 递归子节点标准化：
   ```typescript
   export function normalizeTreeNode(node: any): any {
     return {
       id: String(node.id ?? node.key ?? crypto.randomUUID()),
       name: node.name,
       label: node.label ?? node.name,
       children: node.children?.length ? normalizeTreeNodes(node.children) : undefined,
       leaf: node.children ? node.children.length === 0 : node.leaf,
     }
   }
   ```

3. **`UserPermissions.vue`**：将调用站点从 `normalizeTreeNode`（单节点）切换到 `normalizeTreeNodes`（递归），确保所有嵌套层级均被覆盖。

---

## 测试计划

| 层级 | 测试内容 |
|------|---------|
| 后端单元测试 | `grant_permission` 在服务器崩溃后回滚；`revoke_permissions_batch` 单条 DELETE 影响正确行数 |
| 后端集成测试 | HTTP 500 在 partial-grant 后不产生残留数据 |
| 前端单元测试 | `normalizeTreeNodes` 为 null-id 节点生成唯一键；`normalizeTreeNode` 白名单属性 |
| 前端 E2E | 权限加载失败 → 横幅显示 → 保存按钮禁用；保存后部分失败 → 警告 toast |

---

## 实施顺序

1. 后端 `rbac_service.py` — flush 变更 + 批量 DELETE
2. 后端 `rbac.py` — 事务包裹
3. 前端 `treeNormalizer.ts` — 唯一键 + 白名单
4. 前端 `PermissionAssignmentDrawer.vue` — 加载失败横幅 + 响应检查
5. 前端 `UserPermissions.vue` — 切换到递归标准化
6. 运行完整测试套件（后端 + 前端）
