# 401修复验证指南

## 已完成的代码修复

### 1. 全局Token刷新锁 (`stores/auth.ts`)
```typescript
// 模块级状态（避免拦截器与 store 刷新冲突）
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;
```
- **作用**: 防止多个并发请求同时触发token刷新
- **解决**: 避免refresh_token被重复使用导致的401错误

### 2. 预防性Token刷新 (`stores/auth.ts`)
```typescript
function scheduleTokenRefresh() {
  // 在token过期前10分钟自动刷新
  const refreshDelay = calculateRefreshDelay(timeUntilExpiry, 10 * 60 * 1000);
}
```
- **作用**: 在token过期前主动刷新，避免过期后401
- **解决**: 用户活跃期间不会遇到401

### 3. JWT解析缓存 (`utils/jwt.ts`)
```typescript
const jwtCache = new Map<string, JWTPayload>();
```
- **作用**: 缓存JWT解析结果，减少重复计算
- **优化**: 提升路由守卫检查性能

### 4. Token刷新队列 (`api/request.ts`)
```typescript
let failedQueue: Array<{resolve, reject, config}> = [];
```
- **作用**: 刷新期间排队失败的请求，刷新成功后重试
- **解决**: 避免刷新期间多个请求失败

### 5. 路由守卫优化 (`router/guards.ts`)
```typescript
// 认证信息缓存（5秒TTL）
let cachedAuthInfo: CachedAuthInfo | null = null;

// 迁移检查标记（避免每次路由切换都检查）
let migrationChecked = false;
```
- **作用**: 减少重复storage读取，优化路由切换性能

## 手动验证步骤

### 测试1: 正常登录流程
1. 启动前后端服务: `scripts/start-dev.bat`
2. 访问 http://localhost:5173
3. 使用账号登录: `admin` / `admin123`
4. **预期结果**: 登录成功，跳转工作台

### 测试2: 观察Token刷新
1. 登录后保持页面打开
2. 打开浏览器开发者工具 (F12)
3. 切换到 Network 标签
4. 切换到 Console 标签
5. **观察点**:
   - 10分钟后是否有 `/auth/refresh` 请求
   - Console中是否有 `[Auth] Token 刷新成功` 日志

### 测试3: 并发请求测试
1. 登录后快速切换多个菜单
2. **预期结果**: 所有页面正常加载，无401错误
3. **观察点**: Network中无重复的 `/auth/refresh` 请求

### 测试4: Token过期处理
1. 登录后关闭浏览器
2. 等待30分钟（或手动修改token过期时间）
3. 重新打开页面
4. **预期结果**: 自动跳转登录页，提示"登录已过期"

### 测试5: 无效Token处理
1. 登录后打开控制台
2. 执行: `sessionStorage.setItem('auth_token', 'invalid_token')`
3. 刷新页面
4. **预期结果**: 自动跳转登录页

## API测试命令

使用curl测试后端API:

```bash
# 1. 登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 使用token访问受保护端点
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 测试无效token (应返回401)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid_token"

# 4. 刷新token
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_REFRESH_TOKEN"}'
```

## 常见问题排查

### 问题: 仍然出现401错误
**排查步骤**:
1. 检查后端服务是否运行: `curl http://localhost:8000/api/v1/health`
2. 检查token是否在sessionStorage中: `sessionStorage.getItem('auth_token')`
3. 检查token是否过期: 复制token到 https://jwt.io 查看exp字段
4. 检查refresh_token是否存在: `sessionStorage.getItem('refresh_token')`

### 问题: Token刷新失败
**排查步骤**:
1. 检查后端日志是否有刷新错误
2. 检查refresh_token是否过期（默认30天）
3. 检查数据库中token记录是否被删除

### 问题: 并发请求导致重复刷新
**排查步骤**:
1. 打开浏览器开发者工具
2. 在 `auth.ts` 的 `tryRefreshToken` 函数中添加断点
3. 触发多个请求，观察是否只有一个进入刷新逻辑

## 代码变更清单

| 文件 | 变更类型 | 变更内容 |
|------|---------|---------|
| `frontend/src/stores/auth.ts` | 重构 | 添加全局刷新锁、预防性刷新 |
| `frontend/src/api/request.ts` | 重构 | 添加刷新队列、优化401处理 |
| `frontend/src/utils/jwt.ts` | 新增 | JWT解析和缓存工具 |
| `frontend/src/router/guards.ts` | 优化 | 添加缓存、常量优化 |

## 性能优化效果

| 指标 | 优化前 | 优化后 |
|------|-------|-------|
| 路由切换storage读取 | 2-3次/切换 | 0-1次/切换（缓存）|
| Token刷新并发冲突 | 可能 | 不可能（全局锁）|
| Token过期用户体验 | 突然登出 | 静默刷新 |
| 迁移检查执行 | 每次路由 | 仅首次 |
