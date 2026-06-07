# 前端稳定性三层纵深防御 — 设计文档

**日期**: 2026-06-07
**状态**: 设计已确认，待实现
**作者**: 资深前端架构师

---

## 1. 问题背景

前端频繁出现白屏、组件崩溃、功能失效、控制台报错、偶发性卡顿。根因是**两个问题叠加**：

1. **构建产物不完整** — `resources/frontend/` 与 `frontend/dist/` 不同步，`index.html` 引用的 hash 文件不存在
2. **缺少运行时容错** — 单个 chunk 加载失败导致整个 Vue 应用崩溃白屏

## 2. 架构：三层纵深防御

```
Layer 1: 构建期防护 — sync脚本 → 审计脚本 → 启动前校验 → 阻断不完整部署
Layer 2: 运行时兜底 — ErrorBoundary → chunk重试 → 版本指纹校验 → 优雅降级
Layer 3: 全局异常捕获 — window.onerror → unhandledrejection → API拦截器 → 内存泄漏防护
```

## 3. Layer 1 — 构建期 + 启动期防护

### 3.1 启动前自动校验（`backend/start.py` 增强）

在 `start.py` 的 `main()` → `uvicorn.run()` 之前，增加：

```python
def _verify_frontend_assets():
    """启动前校验前端静态资源完整性。缺失或hash不匹配 → 拒绝启动。"""
    frontend_dir = find_frontend_dir()
    if not frontend_dir:
        print("[WARN] 前端静态资源未找到，启动后仅提供 API 服务")
        return  # 允许纯 API 模式启动

    index_html = os.path.join(frontend_dir, "index.html")
    if not os.path.isfile(index_html):
        print("[FATAL] index.html 缺失，前端无法加载")
        print("  修复: cd frontend && npm run build")
        print("  然后: scripts/build/sync-frontend-dist.bat")
        sys.exit(1)

    # 调用审计脚本的核心逻辑
    from scripts.audit_static_assets import audit
    exit_code = audit(frontend_dir, verbose=False)
    if exit_code != 0:
        print("[FATAL] 静态资源完整性校验失败，拒绝启动")
        print("  修复: cd frontend && npm run build")
        print("  然后: scripts/build/sync-frontend-dist.bat")
        sys.exit(1)
```

### 3.2 构建版本注入（`frontend/public/version.json`）

构建时自动生成，包含版本号 + 时间戳：

```json
{
  "version": "1.3.0",
  "buildTime": "2026-06-07T08:00:00Z",
  "commit": "abc1234"
}
```

### 3.3 Vite 构建钩子

在 `vite.config.ts` 中添加 `generateBundle` 钩子自动生成 `version.json`。

---

## 4. Layer 2 — 运行时兜底

### 4.1 增强 ErrorBoundary（修改 `ErrorBoundary.vue`）

**职责**：捕获所有子组件未处理异常，分类展示降级 UI。

**错误分类**：
- `ChunkLoadError` → "页面模块加载失败" + [重试] 按钮（重新 import）
- `NetworkError` / `TypeError: Failed to fetch` → "网络连接异常" + [刷新页面]
- 其他未知错误 → 错误详情 + [刷新页面] + [回首页]

**关键实现细节**：
- 使用 `onErrorCaptured` 钩子捕获子组件错误
- `error` 参数返回 `false` 阻止错误继续向上传播（防止白屏）
- 非致命错误不阻断，`console.error` 记录后继续运行
- 错误信息包含：时间戳、当前路由、错误类型、堆栈

### 4.2 动态 Import 重试机制（新文件 `useChunkLoader.ts`）

**职责**：包装 Vite 动态 import，失败时自动重试（指数退避）。

```ts
// 接口
function retryImport<T>(
  importFn: () => Promise<T>,
  maxRetries?: number,   // 默认 3
  baseDelay?: number,    // 默认 1000ms
): Promise<T>

// 重试策略：delay * (retryCount)
// 第1次重试: 1s, 第2次: 2s, 第3次: 3s
```

**使用方式**：路由懒加载包装

```ts
// Before
component: () => import('@/views/Workbench.vue')
// After
component: () => retryImport(() => import('@/views/Workbench.vue'))
```

### 4.3 版本指纹校验（新文件 `useVersionCheck.ts`）

**职责**：启动时获取 `/version.json`，比对 localStorage 中上次版本，不一致则强制刷新。

```ts
// 流程
1. 启动时 fetch('/version.json?t=' + Date.now())
2. 读取 localStorage('app_version')
3. 不一致 → 弹提示 "系统已更新，即将刷新" → 1.5s 后 location.reload(true)
4. 一致 → 正常启动
5. 失败（fetch 404）→ 静默跳过，不阻塞启动
```

**触发时机**：`App.vue` 的 `onMounted` 中调用。

---

## 5. Layer 3 — 全局异常捕获

### 5.1 增强全局异常处理（修改 `errorHandler.ts`）

新增 `window.onerror` 监听（现有只有 `unhandledrejection`）：

```ts
export function setupGlobalErrorHandler() {
  // 同步异常
  window.onerror = (message, source, lineno, colno, error) => {
    logger.error("[GlobalError]", { message, source, lineno, colno, error });
    // 非关键错误不阻断用户
    return false; // 让浏览器默认处理
  };

  // 未处理 Promise rejection
  window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason;
    if (reason?.message?.includes("Failed to fetch dynamically imported module")) {
      // ChunkLoadError → 特殊处理
      showToast("页面模块加载失败，请刷新页面重试", "error");
    } else if (reason?.response?.status === 401) {
      // Token 过期
      showToast("登录已过期，请重新登录", "warning");
    } else {
      logger.error("[UnhandledRejection]", reason);
    }
    event.preventDefault();
  });
}
```

### 5.2 API 响应拦截器增强（修改 `api/request.ts`）

```ts
// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    // 成功：确保数据形状安全
    const data = response.data;
    if (data && typeof data === "object") {
      // 数组字段默认值
      if ("items" in data && !Array.isArray(data.items)) data.items = [];
      if ("data" in data && data.data === null) data.data = {};
    }
    return data;
  },
  (error) => {
    // 分类处理错误
    if (error.response) {
      const { status, data } = error.response;
      if (status === 401) { /* token 过期 */ }
      else if (status === 403) { ElMessage.error("权限不足"); }
      else if (status >= 500) { ElMessage.error("服务器异常，请稍后重试"); }
      else { ElMessage.error(data?.detail || "请求失败"); }
    } else if (error.code === "ERR_NETWORK") {
      ElMessage.error("网络连接失败，请检查后端服务");
    } else {
      ElMessage.error("请求异常，请重试");
    }
    return Promise.reject(error);
  }
);
```

### 5.3 安全数据访问工具（新文件 `useSafeData.ts`）

```ts
// 确保 API 返回数据中的嵌套字段安全访问
export function safeArray<T>(value: unknown, fallback: T[] = []): T[] {
  return Array.isArray(value) ? value : fallback;
}
export function safeObject<T>(value: unknown, fallback: T): T {
  return (value && typeof value === "object" && !Array.isArray(value))
    ? (value as T) : fallback;
}
```

### 5.4 内存泄漏修复（5 处）

| 文件 | 问题 | 修复 |
|------|------|------|
| `StatusTag.vue:95` | `setInterval` 未清理 | `onUnmounted` 中 `clearInterval` |
| `SecurityMonitor.vue` | `_monitorInterval` 未清理 | `onUnmounted` 中 `clearInterval` |
| `LoginEnhanced.vue:176` | `carouselInterval` 需确认 | 确认 `onUnmounted` 已清理 ✓ |
| `useResponsiveSidebar.ts:70` | `resize` 监听未清理 | `onUnmounted` 中 `removeEventListener` |
| `useECharts.ts:60` | `resize` 监听 + timer | `onUnmounted` 清理两者 |

---

## 6. 修改文件清单

### 新建文件
| 文件 | 说明 |
|------|------|
| `frontend/public/version.json` | 构建版本指纹 |
| `frontend/src/composables/useChunkLoader.ts` | 动态 import 重试 |
| `frontend/src/composables/useVersionCheck.ts` | 版本指纹校验 |
| `frontend/src/composables/useSafeData.ts` | 安全数据访问工具 |

### 修改文件
| 文件 | 变更内容 |
|------|----------|
| `frontend/vite.config.ts` | `generateBundle` 钩子生成 `version.json` |
| `frontend/src/App.vue` | 集成 `useVersionCheck`；增强 `onErrorCaptured` |
| `frontend/src/components/common/ErrorBoundary.vue` | 重写：分类错误 + 降级 UI + 重试按钮 |
| `frontend/src/utils/errorHandler.ts` | 新增 `window.onerror`；增强 `unhandledrejection` |
| `frontend/src/api/request.ts` | 增强响应拦截器：分类错误 + 脏数据过滤 |
| `frontend/src/router/index.ts` | 路由懒加载包装 `retryImport` |
| `backend/start.py` | 新增 `_verify_frontend_assets()` 启动前校验 |
| `frontend/src/components/ui/StatusTag.vue` | `onUnmounted` 清理 `setInterval` |
| `frontend/src/components/business/SystemStatus.vue` | `onUnmounted` 清理 `setInterval` |
| `frontend/src/composables/useResponsiveSidebar.ts` | `onUnmounted` 清理 `resize` 监听 |
| `frontend/src/composables/useECharts.ts` | `onUnmounted` 清理 `resize` 监听 + timer |

---

## 7. 验证方案

### 7.1 单元测试

| 测试对象 | 测试用例 |
|----------|----------|
| `useChunkLoader` | 首次成功、第2次重试成功、全部失败、超时 |
| `useVersionCheck` | 版本一致跳过、版本不一致弹提示、fetch 失败静默 |
| `useSafeData` | null→[]、undefined→{}、脏对象→默认值 |
| `ErrorBoundary` | ChunkLoadError 显示重试、NetworkError 显示刷新、点击按钮触发重试 |
| `request.ts` 拦截器 | 401→重定向、500→toast、NetworkError→toast |

### 7.2 集成测试

1. **模拟 chunk 404**：删除一个 JS 文件 → 访问对应路由 → 确认显示降级 UI 而非白屏
2. **模拟 API 500**：Mock API 返回 500 → 确认 toast 提示且页面不崩溃
3. **模拟网络断开**：关闭后端 → 访问页面 → 确认不白屏且有提示
4. **内存泄漏验证**：使用 Chrome DevTools Performance Monitor → 反复切换路由 → JS heap 不持续增长

### 7.3 构建验证

```bash
# 1. 故意删除一个 JS 文件
rm resources/frontend/assets/js/some-chunk-*.js

# 2. 启动后端 → 应被阻断
cd backend && python start.py
# 期望: [FATAL] 静态资源完整性校验失败，拒绝启动

# 3. 修复后启动
cd frontend && npm run build
scripts/build/sync-frontend-dist.bat
cd backend && python start.py
# 期望: 正常启动

# 4. 浏览器访问
# 期望: 所有页面正常加载
# 期望: /version.json 可访问，内容正确
```

---

## 8. 风险与回滚

- **低风险**：所有新增功能都是**添加性**的，不修改现有业务逻辑
- **ErrorBoundary 变更**：现有功能简单增强，不改变已有的错误捕获行为
- **路由懒加载包装**：如果 `retryImport` 有问题，fallback 到原始 `import()` 行为
- **回滚方案**：所有改动集中在 12 个文件中，git revert 单次提交即可回滚
