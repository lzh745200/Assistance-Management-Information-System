# 代码审查缺陷修复 — 实施计划

> **对 agentic workers 的要求：** 使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐个任务实施本计划。步骤使用 checkbox (`- [ ]`) 语法进行跟踪。

**目标：** 修复代码审查中发现的 6 个缺陷——批量操作原子性、前端加载故障防御、treeNormalizer 健壮性

**架构：** 后端：将 grant/revoke 端点包裹在 `TransactionManager.transaction(db)` 中；将服务层 `db.commit()` 调用移至 `db.flush()`；将 `revoke_permissions_batch` 重构为单次批量 DELETE + 预查询。前端：添加 `permissionsLoadFailed` 守卫，防止加载失败后意外撤销全部权限；加固 `treeNormalizer`，使用稳定回退键 + 属性白名单

**技术栈：** Python 3.11 / FastAPI / SQLAlchemy + Vue 3 / TypeScript / Element Plus

---

### 任务 1：将 `grant_permission()` 从 `db.commit()` 重构为 `db.flush()`

**文件：**
- 修改：`backend/app/services/rbac_service.py:404-411`

- [ ] **步骤 1：定位 `grant_permission()` 方法中当前的 `db.commit()` 调用**

```bash
grep -n "db.commit()" backend/app/services/rbac_service.py
```
预期：第 411 行附近显示 `db.commit()`

- [ ] **步骤 2：将 `db.commit()` 替换为 `db.flush()`**

在 `backend/app/services/rbac_service.py` 中，`grant_permission()` 方法（约第 404-411 行）：

```python
# 之前（约第 411 行）：
db.commit()

# 之后：
db.flush()
```

- [ ] **步骤 3：运行现有 RBAC 测试以确认无回归**

```bash
cd backend && python -m pytest tests/unit/test_rbac_service.py tests/unit/test_rbac_service_simple.py -v --tb=short
```
预期：全部通过（~18 个测试）

- [ ] **步骤 4：提交**

```bash
git add backend/app/services/rbac_service.py
git commit -m "refactor: grant_permission 改用 db.flush()（调用方拥有事务所有权）"
```

---

### 任务 2：将 `revoke_permissions_batch()` 重构为批量 DELETE + 预查询

**文件：**
- 修改：`backend/app/services/rbac_service.py:432-447`

- [ ] **步骤 1：阅读当前实现**

`revoke_permissions_batch()` 当前在循环中对每个权限调用 `revoke_permission()`（执行独立的 DELETE + COMMIT）。

- [ ] **步骤 2：替换为预查询 + 批量 DELETE 实现**

```python
async def revoke_permissions_batch(
    self, user_id: str, permissions: List[str], db: Session = None
) -> tuple:
    """批量撤销用户权限。返回 (revoked: List[str], failed: List[str])。

    使用预查询确定哪些权限实际存在，然后单条 DELETE 批量删除。
    调用方拥有事务边界（通过 TransactionManager.transaction）。
    """
    uid = int(user_id)

    # 第 1 步：预查询哪些权限对用户实际存在
    from app.models.rbac import UserPermission as UP
    existing_rows = (
        db.query(UP.permission)
        .filter(UP.user_id == uid, UP.permission.in_(permissions))
        .all()
    )
    existing = {row[0] for row in existing_rows}
    missing = [p for p in permissions if p not in existing]

    # 第 2 步：单条批量 DELETE — 仅删除实际存在的权限
    if existing:
        db.query(UP).filter(
            UP.user_id == uid,
            UP.permission.in_(list(existing)),
        ).delete(synchronize_session=False)
        db.flush()

    return list(existing), missing
```

**注意**：移除 `self.revoke_permission()` 的循环调用。此方法现在是自包含的——不再委托给 `revoke_permission()`。

- [ ] **步骤 3：验证文法——无重复导入，`UP` 别名可用**

确认 `UserPermission` 已在文件顶部导入。作为 `rbac_service.py` 的别名导入或使用 `from app.models.rbac import UserPermission`。

- [ ] **步骤 4：运行 RBAC 服务测试**

```bash
cd backend && python -m pytest tests/unit/test_rbac_service.py tests/unit/test_rbac_line_303.py tests/unit/test_rbac_service_simple.py -v --tb=short
```
预期：全部通过

- [ ] **步骤 5：提交**

```bash
git add backend/app/services/rbac_service.py
git commit -m "refactor: 将 revoke_permissions_batch 改为单次批量 DELETE + 预查询"
```

---

### 任务 3：在 `rbac.py` 中为 grant/revoke 端点添加事务包裹

**文件：**
- 修改：`backend/app/api/v1/auth/rbac.py:320-373`

- [ ] **步骤 1：验证导入存在**

确认以下导入位于 `rbac.py` 顶部附近（如不存在则添加）：

```python
from app.core.transaction import TransactionManager
```

- [ ] **步骤 2：为 `grant_permission` 端点添加事务包裹**

替换 `grant_permission` 函数体（约第 320-354 行）：

```python
@router.post("/grant/permission")
async def grant_permission(
    grant: PermissionGrant,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    """直接授予用户权限（支持批量，具有事务原子性）"""
    granted: List[str] = []
    failed: List[str] = []

    user_id_str = str(grant.user_id)
    granted_by_str = str(current_user.id)
    expires_iso = grant.expires_at.isoformat() if grant.expires_at else None

    with TransactionManager.transaction(db) as sess:
        for perm in grant.permissions:
            success = await rbac_service.grant_permission(
                user_id=user_id_str,
                permission=perm,
                granted_by=granted_by_str,
                expires_at=expires_iso,
                db=sess,
            )
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

- [ ] **步骤 3：为 `revoke_permission` 端点添加事务包裹**

替换 `revoke_permission` 函数体（约第 356-373 行）：

```python
@router.post("/revoke/permission")
async def revoke_permission(
    revoke: PermissionGrant,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin()),
):
    """批量撤销用户权限（具有事务原子性）"""
    with TransactionManager.transaction(db) as sess:
        revoked, failed = await rbac_service.revoke_permissions_batch(
            user_id=str(revoke.user_id),
            permissions=revoke.permissions,
            db=sess,
        )

    return {
        "success": len(failed) == 0,
        "revoked": revoked,
        "failed": failed,
        "message": f"权限撤销完成: 成功 {len(revoked)}, 失败 {len(failed)}",
    }
```

- [ ] **步骤 4：运行所有 RBAC 相关测试**

```bash
cd backend && python -m pytest tests/unit/test_rbac_service.py tests/unit/test_rbac_line_303.py tests/unit/test_rbac_service_simple.py tests/unit/test_user_permission_service.py -v --tb=short
```
预期：全部通过（~170 个测试）

- [ ] **步骤 5：提交**

```bash
git add backend/app/api/v1/auth/rbac.py
git commit -m "fix: 为 grant/revoke 端点包裹 TransactionManager.transaction 以确保原子性"
```

---

### 任务 4：加固 `treeNormalizer.ts` — 稳定回退键 + 白名单 + 递归

**文件：**
- 修改：`frontend/src/utils/treeNormalizer.ts`

- [ ] **步骤 1：阅读当前文件**

确认文件存在于 `frontend/src/utils/treeNormalizer.ts`。

- [ ] **步骤 2：添加 `makeStableId` 辅助函数并重写导出**

完整替换文件内容：

```typescript
/**
 * 组织树节点规范化工具
 *
 * 解决 Element Plus el-tree / el-tree-select 无法处理数值型 id 的问题：
 * el-tree 内部通过 setAttribute('id', ...) 设置 DOM id 属性，
 * 当 id 为 0 或纯数字时触发 DOMException: "'0' is not a valid attribute name"
 *
 * 根因修复建议：后端 API 返回 id 为字符串（在路由/服务层统一转换）
 * 当前前端侧统一用此工具兜底。
 */

/** 生成稳定的、基于内容的回退键 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function makeStableId(node: any): string {
  return String(
    node.id ??
    node.key ??
    `_node_${(node.name || node.label || '').substring(0, 20)}`
  );
}

/** 将单节点 id 转为字符串，白名单属性，递归标准化子节点 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
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

/** 递归规范化整棵树 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeTreeNodes(nodes: any[]): any[] {
  return nodes.map(node => normalizeTreeNode(node));
}
```

- [ ] **步骤 3：检查前端类型**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1
```
预期：无错误

- [ ] **步骤 4：提交**

```bash
git add frontend/src/utils/treeNormalizer.ts
git commit -m "fix: 加固 treeNormalizer — 稳定回退键 + 属性白名单 + 递归标准化"
```

---

### 任务 5：为 `PermissionAssignmentDrawer.vue` 添加加载故障防御

**文件：**
- 修改：`frontend/src/components/permission/PermissionAssignmentDrawer.vue:145-247`

- [ ] **步骤 1：添加 `permissionsLoadFailed` 状态**

在 `<script setup>` 块中，在其他 `ref` 声明附近（约第 150 行之后）：

```typescript
const permissionsLoadFailed = ref(false);
```

- [ ] **步骤 2：更新 `loadCurrentPermissions` — 成功/失败分支**

替换 `loadCurrentPermissions` 函数（约第 172-183 行）：

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
    // currentPermissions 保留既有值——不覆写为 []
  }
}
```

- [ ] **步骤 3：在权限树上方添加警告横幅模板**

在 `<el-tab-pane label="权限配置" name="permissions">` 内部，`<PermissionTreePanel>` 之前添加（约第 23 行之后）：

```html
<el-alert
  v-if="permissionsLoadFailed"
  type="warning"
  :closable="false"
  show-icon
  style="margin-bottom: 12px"
>
  权限数据加载失败，请关闭面板后重试。保存操作已被禁用。
</el-alert>
```

- [ ] **步骤 4：禁用保存按钮**

将保存按钮（约第 28-35 行）从：

```html
<el-button
  type="primary"
  :loading="savingPermissions"
  @click="savePermissions"
>
  保存权限
</el-button>
```

改为：

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

- [ ] **步骤 5：更新 `savePermissions` — 添加守卫 + 增强响应检查**

替换 `savePermissions` 函数（约第 214-246 行）：

```typescript
async function savePermissions() {
  if (!props.user?.id || permissionsLoadFailed.value) return;
  savingPermissions.value = true;
  try {
    // 1. 撤销已移除的权限
    const existingRes = await request.get(`/rbac/user/${props.user.id}/permissions`);
    const existingPayload = existingRes.data?.data || existingRes.data;
    const existingPerms: string[] = existingPayload?.permissions || [];
    const toRevoke = existingPerms.filter(
      (p: string) => !currentPermissions.value.includes(p)
    );
    if (toRevoke.length > 0) {
      await request.post("/rbac/revoke/permission", {
        user_id: props.user.id,
        permissions: toRevoke,
      });
    }
    // 2. 授予当前权限
    const res = await request.post("/rbac/grant/permission", {
      user_id: props.user.id,
      permissions: currentPermissions.value,
    });
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

- [ ] **步骤 6：类型检查**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1
```
预期：无错误

- [ ] **步骤 7：提交**

```bash
git add frontend/src/components/permission/PermissionAssignmentDrawer.vue
git commit -m "fix: 添加 permissionsLoadFailed 守卫 — 防止加载失败后意外清空权限"
```

---

### 任务 6：将 `UserPermissions.vue` 切换为递归 treeNormalizer

**文件：**
- 修改：`frontend/src/views/system/UserPermissions.vue:458,469,487`

- [ ] **步骤 1：验证导入使用 `normalizeTreeNodes`**

确认第 458 行的导入为：

```typescript
import { normalizeTreeNodes } from "@/utils/treeNormalizer";
```

若当前导入的是 `normalizeTreeNode`（单数），则替换为 `normalizeTreeNodes`。

- [ ] **步骤 2：在两个 `loadNode` 调用点使用递归标准化**

`loadNode` 中（约第 469 和 487 行），确保：

```typescript
resolve(res.data.map(node => normalizeTreeNode(node)));
```

替换为：

```typescript
resolve(normalizeTreeNodes(res.data));
```

这确保所有嵌套层级均被标准化，同时 `normalizeTreeNodes` 通过 `normalizeTreeNode` 应用白名单。

- [ ] **步骤 3：类型检查**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1
```
预期：无错误

- [ ] **步骤 4：提交**

```bash
git add frontend/src/views/system/UserPermissions.vue
git commit -m "fix: 将 UserPermissions 树切换为递归 treeNormalizer 以覆盖深层嵌套"
```

---

### 任务 7：全量回归测试

**文件：** 无（仅测试运行）

- [ ] **步骤 1：运行完整后端测试套件**

```bash
cd backend && python -m pytest tests/ -x --tb=short -q 2>&1 | tail -20
```
预期：7314 通过，0 失败（1 个预存在的 failure 属于无关测试 `test_check_permission_no_db`）

- [ ] **步骤 2：运行完整前端测试套件**

```bash
cd frontend && npx vitest run 2>&1 | tail -10
```
预期：1696 通过，149 个测试文件全部通过

- [ ] **步骤 3：手动验证关键流程**

启动后端和前端，验证：
1. 在 `/system/users` 页面，点击用户的"角色/权限" → 权限 Tab 正确加载
2. 切换权限复选框，保存 → 操作成功 toast
3. 重新打开同一用户的抽屉 → 权限状态持久化

- [ ] **步骤 4：最终提交（如有清理需要）**

```bash
git status
# 仅在存在未提交的测试修正或清理时提交
```

---

### 任务 8（可选）：添加事务回滚的单元测试

**文件：**
- 创建：`backend/tests/unit/test_rbac_transaction.py`

- [ ] **步骤 1：写入测试以验证回滚行为**

```python
"""测试 RBAC 批量操作的事务原子性"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.rbac_service import rbac_service


class TestGrantPermissionTransaction:
    """验证在事务中 flush 的 grant_permission 行为"""

    def test_flush_called_instead_of_commit(self):
        """grant_permission 应调用 db.flush()，而非 db.commit()"""
        mock_db = MagicMock()
        # 模拟无已存在权限
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        # 应不抛出异常
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            rbac_service.grant_permission(
                user_id="1", permission="user:read",
                granted_by="1", db=mock_db)
        )
        assert result is True
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_not_called()


class TestRevokePermissionsBatch:
    """验证预查询 + 批量 DELETE 的正确性"""

    def test_returns_revoked_and_failed_lists(self):
        """应正确拆分已撤销/失败的权限"""
        mock_db = MagicMock()
        # 模拟：3 个权限中，只有 'user:read' 和 'village:write' 存在
        mock_db.query.return_value.filter.return_value.all.return_value = [
            ("user:read",), ("village:write",)
        ]

        import asyncio
        revoked, failed = asyncio.get_event_loop().run_until_complete(
            rbac_service.revoke_permissions_batch(
                user_id="1",
                permissions=["user:read", "village:write", "not:exist"],
                db=mock_db)
        )

        assert set(revoked) == {"user:read", "village:write"}
        assert failed == ["not:exist"]

    def test_nonexistent_permissions_all_failed(self):
        """当无权限存在时，全部应返回为 failed"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        import asyncio
        revoked, failed = asyncio.get_event_loop().run_until_complete(
            rbac_service.revoke_permissions_batch(
                user_id="1",
                permissions=["not:exist1", "not:exist2"],
                db=mock_db)
        )

        assert revoked == []
        assert set(failed) == {"not:exist1", "not:exist2"}
```

- [ ] **步骤 2：运行新测试**

```bash
cd backend && python -m pytest tests/unit/test_rbac_transaction.py -v --tb=short
```
预期：3 通过

- [ ] **步骤 3：提交**

```bash
git add backend/tests/unit/test_rbac_transaction.py
git commit -m "test: 为批量 RBAC 操作添加事务原子性测试"
```

---

## 摘要：提交链

| 提交 | 文件 | 消息 |
|------|------|------|
| 1 | `rbac_service.py` | `refactor: grant_permission 改用 db.flush()（调用方拥有事务所有权）` |
| 2 | `rbac_service.py` | `refactor: 将 revoke_permissions_batch 改为单次批量 DELETE + 预查询` |
| 3 | `rbac.py` | `fix: 为 grant/revoke 端点包裹 TransactionManager.transaction 以确保原子性` |
| 4 | `treeNormalizer.ts` | `fix: 加固 treeNormalizer — 稳定回退键 + 属性白名单 + 递归标准化` |
| 5 | `PermissionAssignmentDrawer.vue` | `fix: 添加 permissionsLoadFailed 守卫 — 防止加载失败后意外清空权限` |
| 6 | `UserPermissions.vue` | `fix: 将 UserPermissions 树切换为递归 treeNormalizer 以覆盖深层嵌套` |
| 7 | 测试运行 | （验证——仅当全部通过时才提交） |
| 8 | `test_rbac_transaction.py` | `test: 为批量 RBAC 操作添加事务原子性测试` |
