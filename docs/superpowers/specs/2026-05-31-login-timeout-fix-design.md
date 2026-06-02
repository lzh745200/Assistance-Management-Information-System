# 登录超时修复设计

**日期**: 2026-05-31
**状态**: 已批准
**分支**: master

## 问题

登录请求超时 "timeout of 30000ms exceeded"，第一次登录必现。

## 根因

bcrypt 5.x 移除了 `__about__` 模块，passlib 在加载时尝试访问
`_bcrypt.__about__.__version__` 抛出 `AttributeError`，回退到纯 Python
bcrypt 实现，密码验证耗时 20-60 秒，超过 Axios 30 秒超时。

次要原因：`MachineCodeService.get_machine_code()` 每次登录 fork 3 个
`wmic` 子进程（CPU/主板/磁盘），增加数秒延迟。

## 方案（方案 A：根治）

### 变更 1: bcrypt 5.x 兼容性修复

- **文件**: `backend/app/core/security.py`
- **改动**: 在现有 `_finalize_backend_mixin` 补丁之前，注入 `_bcrypt.__about__`
  使 passlib 能正常加载 C 扩展
- **效果**: `verify_password()` 从 ~30s → ~100ms

### 变更 2: 机器码进程级缓存

- **文件**: `backend/app/services/machine_code_service.py`
- **改动**: `get_machine_code()` 添加模块级缓存，首次计算后复用
- **效果**: 每次登录节省 3 次 `wmic` 子进程调用

### 变更 3: 登录专用超时（兜底）

- **文件**: `frontend/src/stores/auth.ts`
- **改动**: 登录 POST 请求单独配置 60s timeout
- **效果**: 防止极端场景下仍超时

## 验证

- [ ] `verify_password()` 在 bcrypt 5.x 下 < 200ms
- [ ] `get_machine_code()` 第二次调用直接返回缓存值
- [ ] 后端测试全部通过
- [ ] 实际登录测试通过
