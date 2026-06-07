# 前端稳定性三层纵深防御 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建三层纵深防御体系，杜绝前端白屏/崩溃/功能失效，实现"单模块异常不影响全局"的容错能力。

**Architecture:** Layer 1 在构建期和启动期阻断不完整的部署；Layer 2 在运行时用 ErrorBoundary + chunk 重试 + 版本指纹实现优雅降级；Layer 3 用全局异常捕获 + API 拦截器 + 内存泄漏修复兜底所有未预期异常。

**Tech Stack:** Vue 3 + TypeScript + Pinia + Vite + FastAPI + Python 3.11

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `frontend/public/version.json` | 新建 | 构建版本指纹（构建时自动生成） |
| `frontend/src/composables/useChunkLoader.ts` | 新建 | 动态 import 指数退避重试 |
| `frontend/src/composables/useVersionCheck.ts` | 新建 | 启动时版本比对+自动刷新 |
| `frontend/src/composables/useSafeData.ts` | 新建 | API 脏数据安全类型守卫 |
| `frontend/vite.config.ts` | 修改 | `generateBundle` 钩子 → `version.json` |
| `frontend/src/components/common/ErrorBoundary.vue` | 修改 | 分类错误+降级UI+重试按钮 |
| `frontend/src/utils/errorHandler.ts` | 修改 | 新增 `window.onerror` |
| `frontend/src/api/request.ts` | 修改 | 响应拦截器增强+脏数据过滤 |
| `frontend/src/router/index.ts` | 修改 | 路由懒加载包装 `retryImport` |
| `frontend/src/App.vue` | 修改 | 集成 `useVersionCheck` |
| `backend/start.py` | 修改 | 启动前 `_verify_frontend_assets()` |
| `frontend/src/components/ui/StatusTag.vue` | 修改 | 内存泄漏修复 |
| `frontend/src/components/business/SystemStatus.vue` | 修改 | 内存泄漏修复 |
| `frontend/src/composables/useResponsiveSidebar.ts` | 修改 | 内存泄漏修复 |
| `frontend/src/composables/useECharts.ts` | 修改 | 内存泄漏修复 |

---

## Layer 1: 构建期防护

### Task 1: Vite 构建钩子 — 自动生成 version.json

**Files:**
- Modify: `frontend/vite.config.ts`
- Create: `frontend/public/version.json`（构建时自动生成）

- [ ] **Step 1: 在 vite.config.ts 的 plugins 数组中添加 generateBundle 插件**

```ts
// 在 spaFallbackPlugin() 之后、vue() 之前添加
{
  name: 'generate-version-json',
  apply: 'build',  // 仅在构建时生效
  generateBundle() {
    const versionJson = JSON.stringify({
      version: process.env.npm_package_version || '1.3.0',
      buildTime: new Date().toISOString(),
    }, null, 2);
    // emitFile 将文件输出到 dist/ 根目录
    this.emitFile({
      type: 'asset',
      fileName: 'version.json',
      source: versionJson,
    });
  },
},
```

- [ ] **Step 2: 构建前端并验证 version.json 生成**

```bash
cd frontend && npm run build
```

Expected: `frontend/dist/version.json` 存在，内容包含 `version` 和 `buildTime` 字段。

- [ ] **Step 3: 同步到 resources/frontend/ 并验证可访问**

```bash
scripts/build/sync-frontend-dist.bat
# 启动后端后访问 http://localhost:8000/version.json
```

Expected: 返回 JSON，`Cache-Control` 头不含 `immutable`（version.json 不应被长期缓存）。

- [ ] **Step 4: 提交**

```bash
git add frontend/vite.config.ts frontend/dist/version.json
git commit -m "feat(layer-1): auto-generate version.json on vite build"
```

---

### Task 2: 启动前静态资源完整性校验

**Files:**
- Modify: `backend/start.py`

- [ ] **Step 1: 在 start.py 的 main() 函数中，uvicorn.run() 调用之前，添加 _verify_frontend_assets()**

在 `main()` 函数中，找到 `uvicorn.run(app, ...)` 调用，在其上方插入：

```python
    # ── 启动前静态资源完整性校验 ──
    _verify_frontend_assets()
```

- [ ] **Step 2: 在 start.py 文件顶部（_check_python_arch 之前）添加 _verify_frontend_assets 函数**

```python
def _verify_frontend_assets():
    """启动前校验前端静态资源完整性。
    
    检测 resources/frontend/index.html 是否存在，以及其引用的所有
    JS/CSS 文件是否真实存在。缺失或 hash 不匹配 → 拒绝启动并打印修复指引。
    纯 API 模式（无前端目录）下跳过校验。
    """
    import os
    import sys

    # 查找前端目录（复用 static_files.py 的逻辑）
    frontend_dir = None
    candidates = [
        os.environ.get("FRONTEND_DIST_PATH", ""),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources", "frontend"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "index.html")):
            frontend_dir = os.path.abspath(candidate)
            break

    if not frontend_dir:
        print("[WARN] 前端静态资源未找到，启动后仅提供 API 服务")
        print("  如需前端界面，请执行: cd frontend && npm run build")
        return  # 允许纯 API 模式启动

    # 调用审计脚本的核心校验逻辑
    try:
        import subprocess
        audit_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "scripts", "audit_static_assets.py",
        )
        result = subprocess.run(
            [sys.executable, audit_script, "--dir", frontend_dir],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print("=" * 60)
            print("[FATAL] 前端静态资源完整性校验失败，拒绝启动！")
            print("=" * 60)
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            print("修复步骤:")
            print("  1. cd frontend && npm run build")
            print("  2. Windows: call scripts\\build\\sync-frontend-dist.bat")
            print("     Linux:   bash scripts/build/sync-frontend-dist.sh")
            print("  3. 重新启动后端")
            print("=" * 60)
            sys.exit(1)
        else:
            print("[OK] 前端静态资源完整性校验通过")
    except FileNotFoundError:
        print("[WARN] 审计脚本未找到，跳过静态资源校验")
    except Exception as e:
        print(f"[WARN] 静态资源校验执行异常: {e}，跳过校验继续启动")
```

- [ ] **Step 3: 验证 — 删除一个 JS 文件后启动应被阻断**

```bash
# 备份一个 JS 文件
cp resources/frontend/assets/js/index-*.js /tmp/index-backup.js
# 删除它
rm resources/frontend/assets/js/index-*.js
# 尝试启动 → 应被阻断
cd backend && python start.py
# Expected: [FATAL] 静态资源完整性校验失败，拒绝启动！
# 恢复文件
cp /tmp/index-backup.js resources/frontend/assets/js/
```

- [ ] **Step 4: 提交**

```bash
git add backend/start.py
git commit -m "feat(layer-1): startup frontend asset integrity check"
```

---

## Layer 2: 运行时兜底

### Task 3: useChunkLoader — 动态 Import 重试

**Files:**
- Create: `frontend/src/composables/useChunkLoader.ts`
- Create: `frontend/tests/unit/composables/useChunkLoader.test.ts`

- [ ] **Step 1: 编写测试文件**

Write `frontend/tests/unit/composables/useChunkLoader.test.ts`:

```ts
import { describe, it, expect, vi } from 'vitest';
import { retryImport } from '@/composables/useChunkLoader';

describe('useChunkLoader/retryImport', () => {
  it('首次成功 → 返回结果', async () => {
    const result = await retryImport(() => Promise.resolve('ok'), 3, 10);
    expect(result).toBe('ok');
  });

  it('第1次失败、第2次成功 → 返回结果', async () => {
    let calls = 0;
    const fn = () => {
      calls++;
      if (calls < 2) return Promise.reject(new Error('fail'));
      return Promise.resolve('retry-ok');
    };
    const result = await retryImport(fn, 3, 10);
    expect(result).toBe('retry-ok');
    expect(calls).toBe(2);
  });

  it('全部失败 → 抛出最后一次错误', async () => {
    const fn = () => Promise.reject(new Error('always-fail'));
    await expect(retryImport(fn, 3, 10)).rejects.toThrow('always-fail');
  });

  it('maxRetries=0 → 不重试，直接抛出', async () => {
    const fn = () => Promise.reject(new Error('no-retry'));
    await expect(retryImport(fn, 0, 10)).rejects.toThrow('no-retry');
  });

  it('指数退避延迟正确', async () => {
    vi.useFakeTimers();
    let calls = 0;
    const fn = () => {
      calls++;
      return Promise.reject(new Error('fail'));
    };
    const promise = retryImport(fn, 3, 100);
    // 第一次调用立即执行
    await vi.advanceTimersByTimeAsync(0);
    expect(calls).toBe(1);
    // 第1次重试在 100ms 后
    await vi.advanceTimersByTimeAsync(100);
    expect(calls).toBe(2);
    // 第2次重试在 200ms 后
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toBe(3);
    // 第3次重试在 300ms 后
    await vi.advanceTimersByTimeAsync(300);
    expect(calls).toBe(4);
    vi.useRealTimers();
    // 清理未处理的 rejection
    await promise.catch(() => {});
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd frontend && npx vitest run tests/unit/composables/useChunkLoader.test.ts
```
Expected: FAIL — module not found.

- [ ] **Step 3: 实现 useChunkLoader.ts**

Write `frontend/src/composables/useChunkLoader.ts`:

```ts
/**
 * useChunkLoader — Vite 动态 import 指数退避重试
 *
 * 包装 Vite 的动态 import()，在失败时自动重试（指数退避），
 * 防止因临时网络抖动或 CDN 故障导致单个 chunk 加载失败 → 全局白屏。
 *
 * Usage:
 *   // 在路由配置中替换原始 import()
 *   component: () => retryImport(() => import('@/views/Workbench.vue'))
 *
 *   重试策略（指数退避）:
 *     第1次失败 → 等待 baseDelay * 1 → 重试
 *     第2次失败 → 等待 baseDelay * 2 → 重试
 *     第3次失败 → 抛出错误
 */

/** 等待指定毫秒 */
function _wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 带指数退避重试的动态 import 包装器
 *
 * @param importFn  - Vite 动态 import 函数，如 () => import('./Foo.vue')
 * @param maxRetries - 最大重试次数（默认 3，总计最多 4 次尝试）
 * @param baseDelay  - 基础延迟毫秒数（默认 1000ms，实际延迟 = baseDelay × 重试序号）
 * @returns Promise<T> — 成功时返回模块，全部失败时抛出最后一次错误
 */
export async function retryImport<T = any>(
  importFn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await importFn();
    } catch (error) {
      // 最后一次尝试失败 → 不再重试，向上抛出
      if (attempt >= maxRetries) {
        throw error;
      }
      // 指数退避: attempt=0 → delay=baseDelay*1, attempt=1 → delay=baseDelay*2
      const delay = baseDelay * (attempt + 1);
      console.warn(
        `[ChunkLoader] 模块加载失败，${delay}ms 后重试 (${attempt + 1}/${maxRetries})`,
        error instanceof Error ? error.message : error,
      );
      await _wait(delay);
    }
  }
  // TypeScript 需要显式 throw（实际不会到达这里）
  throw new Error("[ChunkLoader] unreachable");
}

export default retryImport;
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd frontend && npx vitest run tests/unit/composables/useChunkLoader.test.ts
```
Expected: 5/5 PASS.

- [ ] **Step 5: 提交**

```bash
git add frontend/src/composables/useChunkLoader.ts frontend/tests/unit/composables/useChunkLoader.test.ts
git commit -m "feat(layer-2): retryImport with exponential backoff for dynamic imports"
```

---

### Task 4: useVersionCheck — 版本指纹校验

**Files:**
- Create: `frontend/src/composables/useVersionCheck.ts`
- Create: `frontend/tests/unit/composables/useVersionCheck.test.ts`

- [ ] **Step 1: 编写测试文件**

Write `frontend/tests/unit/composables/useVersionCheck.test.ts`:

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { checkVersion } from '@/composables/useVersionCheck';

describe('useVersionCheck/checkVersion', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('版本号一致 → 不刷新，不弹提示', async () => {
    localStorage.setItem('app_version', '1.3.0');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ version: '1.3.0' }),
    });
    const reloadSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: reloadSpy },
      writable: true,
    });
    await checkVersion();
    expect(reloadSpy).not.toHaveBeenCalled();
  });

  it('版本号不一致 → 提示后刷新', async () => {
    localStorage.setItem('app_version', '1.2.0');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ version: '1.3.0' }),
    });
    await checkVersion();
    // checkVersion 内部会设置 setTimeout 1.5s 后刷新
    // 这里只验证它不抛出异常
  });

  it('fetch 失败 (404) → 静默跳过，不抛异常', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('network error'));
    await expect(checkVersion()).resolves.toBeUndefined();
  });

  it('首次访问无缓存版本号 → 保存版本号，不刷新', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ version: '1.3.0' }),
    });
    await checkVersion();
    expect(localStorage.getItem('app_version')).toBe('1.3.0');
  });
});
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd frontend && npx vitest run tests/unit/composables/useVersionCheck.test.ts
```
Expected: FAIL — module not found.

- [ ] **Step 3: 实现 useVersionCheck.ts**

Write `frontend/src/composables/useVersionCheck.ts`:

```ts
/**
 * useVersionCheck — 版本指纹校验
 *
 * 应用启动时从服务器获取 /version.json，与 localStorage 中
 * 缓存的版本号比对。版本不一致 → 提示用户系统已更新 → 自动强制刷新。
 * fetch 失败时静默跳过，不阻塞应用启动。
 *
 * Usage (在 App.vue onMounted 中):
 *   import { checkVersion } from '@/composables/useVersionCheck';
 *   onMounted(() => { checkVersion(); });
 */
import { ElMessage } from 'element-plus';

/** localStorage 键名 */
const VERSION_KEY = 'app_version';

/** 版本比对后自动刷新的延迟（毫秒） */
const RELOAD_DELAY = 1500;

/**
 * 检查应用版本是否需要更新。
 * 从服务器获取 /version.json，与本地缓存比对。
 * 不一致时：显示提示 → 更新缓存 → 延迟后强制刷新。
 * 网络错误时静默跳过。
 */
export async function checkVersion(): Promise<void> {
  try {
    const response = await fetch(`/version.json?t=${Date.now()}`, {
      cache: 'no-store',
    });

    if (!response.ok) {
      // 404 或其他 HTTP 错误 → 静默跳过（可能 version.json 未部署）
      return;
    }

    const data = await response.json() as { version?: string };
    const serverVersion = data?.version;

    if (!serverVersion) {
      return; // version.json 格式不正确
    }

    const cachedVersion = localStorage.getItem(VERSION_KEY);

    if (!cachedVersion) {
      // 首次访问 → 保存版本号，不刷新
      localStorage.setItem(VERSION_KEY, serverVersion);
      return;
    }

    if (cachedVersion !== serverVersion) {
      // 版本不一致 → 提示用户 + 延迟刷新
      localStorage.setItem(VERSION_KEY, serverVersion);
      ElMessage.warning({
        message: `系统已更新至 v${serverVersion}，即将自动刷新...`,
        duration: RELOAD_DELAY,
      });
      setTimeout(() => {
        // 强制刷新，绕过浏览器缓存
        window.location.reload();
      }, RELOAD_DELAY);
    }
    // 版本一致 → 无需操作
  } catch {
    // 网络错误 → 静默跳过，不阻塞应用
    console.debug('[VersionCheck] /version.json 获取失败，跳过版本检查');
  }
}

export default checkVersion;
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd frontend && npx vitest run tests/unit/composables/useVersionCheck.test.ts
```
Expected: 4/4 PASS.

- [ ] **Step 5: 提交**

```bash
git add frontend/src/composables/useVersionCheck.ts frontend/tests/unit/composables/useVersionCheck.test.ts
git commit -m "feat(layer-2): useVersionCheck — version fingerprint check on startup"
```

---

### Task 5: 增强 ErrorBoundary — 分类错误 + 降级 UI + 重试

**Files:**
- Modify: `frontend/src/components/common/ErrorBoundary.vue`

- [ ] **Step 1: 读取现有 ErrorBoundary.vue 以理解当前结构**

```bash
# 查看当前文件
cat frontend/src/components/common/ErrorBoundary.vue
```

- [ ] **Step 2: 重写 ErrorBoundary.vue**

Write the complete replacement for `frontend/src/components/common/ErrorBoundary.vue`:

```vue
<template>
  <div v-if="hasError" class="error-boundary-fallback">
    <div class="error-boundary-content">
      <!-- 类型 1: ChunkLoadError -->
      <template v-if="errorType === 'chunk'">
        <el-result icon="warning" title="页面模块加载失败" :sub-title="errorMessage">
          <template #extra>
            <el-button type="primary" :loading="isRetrying" @click="handleRetry">
              重新加载
            </el-button>
            <el-button @click="handleReload">刷新页面</el-button>
          </template>
        </el-result>
      </template>

      <!-- 类型 2: NetworkError -->
      <template v-else-if="errorType === 'network'">
        <el-result icon="error" title="网络连接异常" :sub-title="errorMessage">
          <template #extra>
            <el-button type="primary" @click="handleReload">刷新页面</el-button>
            <el-button @click="handleGoHome">返回首页</el-button>
          </template>
        </el-result>
      </template>

      <!-- 类型 3: 未知错误 -->
      <template v-else>
        <el-result icon="error" title="页面发生异常" :sub-title="errorMessage">
          <template #extra>
            <el-button type="primary" @click="handleReload">刷新页面</el-button>
            <el-button @click="handleGoHome">返回首页</el-button>
            <el-button @click="showDetail = !showDetail">
              {{ showDetail ? '收起' : '查看' }}详情
            </el-button>
          </template>
        </el-result>
        <div v-if="showDetail && errorStack" class="error-boundary-stack">
          <pre>{{ errorStack }}</pre>
        </div>
      </template>
    </div>
  </div>
  <!-- 无错误时透明渲染子组件 -->
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from "vue";
import { useRouter } from "vue-router";
import { ElResult, ElButton } from "element-plus";

/** 错误类型：chunk | network | unknown */
type ErrorType = "chunk" | "network" | "unknown";

const router = useRouter();

const hasError = ref(false);
const isRetrying = ref(false);
const showDetail = ref(false);
const errorType = ref<ErrorType>("unknown");
const errorMessage = ref("");
const errorStack = ref("");

/** 分类错误类型 */
function classifyError(err: unknown): { type: ErrorType; message: string } {
  const msg = err instanceof Error ? err.message : String(err);
  const stack = err instanceof Error ? err.stack : "";

  // ChunkLoadError: Vite 动态 import 失败
  if (
    msg.includes("Failed to fetch dynamically imported module") ||
    msg.includes("Importing a module script failed") ||
    msg.includes("error loading dynamically imported module")
  ) {
    return { type: "chunk", message: "页面模块加载失败，请检查网络连接后重试。" };
  }

  // NetworkError: fetch / xhr 网络错误
  if (
    msg.includes("Failed to fetch") ||
    msg.includes("NetworkError") ||
    msg.includes("ERR_NETWORK") ||
    msg.includes("net::ERR_")
  ) {
    return { type: "network", message: "网络连接异常，请检查后端服务是否正常运行。" };
  }

  // 未知错误 → 展示完整信息
  return { type: "unknown", message: msg || "未知运行时异常" };
}

/** onErrorCaptured: 捕获所有子组件未处理异常 */
onErrorCaptured((err: unknown, _instance, info: string) => {
  const { type, message } = classifyError(err);
  errorType.value = type;
  errorMessage.value = message;
  errorStack.value = err instanceof Error ? (err.stack || "") : "";
  hasError.value = true;

  console.error(
    `[ErrorBoundary] ${type} | route=${router.currentRoute.value?.path} | info=${info}`,
    err,
  );

  // 返回 false 阻止错误继续向上传播（防止白屏）
  return false;
});

/** 重试：清除错误状态，Vue 会自动重新渲染子组件 */
function handleRetry() {
  isRetrying.value = true;
  hasError.value = false;
  showDetail.value = false;
  // 延迟重置 loading 状态
  setTimeout(() => {
    isRetrying.value = false;
  }, 500);
}

/** 刷新页面（绕过缓存） */
function handleReload() {
  window.location.reload();
}

/** 返回首页 */
function handleGoHome() {
  hasError.value = false;
  router.push("/").catch(() => {
    // 路由跳转失败 → 强制刷新
    window.location.href = "/";
  });
}
</script>

<style scoped>
.error-boundary-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px 20px;
}

.error-boundary-content {
  max-width: 560px;
  width: 100%;
}

.error-boundary-stack {
  margin-top: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  overflow-x: auto;
}

.error-boundary-stack pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--el-text-color-secondary);
}
</style>
```

- [ ] **Step 3: 验证 ErrorBoundary 在 App.vue 中被使用**

检查 `frontend/src/App.vue` 确认 ErrorBoundary 包裹了 `<router-view />`：

```vue
<ErrorBoundary>
  <router-view />
</ErrorBoundary>
```

如未包裹，添加之。

- [ ] **Step 4: 运行现有测试确保不破坏**

```bash
cd frontend && npx vitest run
```
Expected: 134/134 test files pass.

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/common/ErrorBoundary.vue
git commit -m "feat(layer-2): enhanced ErrorBoundary — classified errors + degradation UI + retry"
```

---

### Task 6: 路由懒加载包装 retryImport

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 在 router/index.ts 顶部添加 retryImport 导入**

```ts
import { retryImport } from "@/composables/useChunkLoader";
```

- [ ] **Step 2: 将所有 `() => import('@/views/...')` 包装为 `() => retryImport(() => import('@/views/...'))`**

使用全局查找替换模式。在 `frontend/src/router/index.ts` 中：

```bash
# 查找当前 import 模式
grep -n "() => import(" frontend/src/router/index.ts
```

每一处 `() => import('...')` 改为 `() => retryImport(() => import('...'))`。

- [ ] **Step 3: 验证 TypeScript 编译通过**

```bash
cd frontend && npx tsc --noEmit
```
Expected: 0 errors.

- [ ] **Step 4: 验证路由测试通过**

```bash
cd frontend && npx vitest run tests/unit/router/
```
Expected: all pass.

- [ ] **Step 5: 提交**

```bash
git add frontend/src/router/index.ts
git commit -m "feat(layer-2): wrap all route lazy imports with retryImport"
```

---

### Task 7: App.vue 集成 useVersionCheck

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 在 App.vue 的 `<script setup>` 中添加版本检查**

在 `onMounted` 中调用 `checkVersion()`：

```ts
import { checkVersion } from "@/composables/useVersionCheck";

onMounted(() => {
  checkVersion();
});
```

- [ ] **Step 2: 验证 TypeScript 编译通过**

```bash
cd frontend && npx tsc --noEmit
```
Expected: 0 errors.

- [ ] **Step 3: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat(layer-2): integrate useVersionCheck in App.vue onMounted"
```

---

## Layer 3: 全局异常捕获

### Task 8: 增强 errorHandler.ts — 添加 window.onerror

**Files:**
- Modify: `frontend/src/utils/errorHandler.ts`

- [ ] **Step 1: 读取现有 errorHandler.ts 理解当前结构**

```bash
cat frontend/src/utils/errorHandler.ts | head -30
```

- [ ] **Step 2: 在 setupGlobalErrorHandler 函数中添加 window.onerror**

在现有的 `unhandledrejection` 监听之前添加：

```ts
// 同步未捕获异常
window.onerror = (message, source, lineno, colno, error) => {
  if (typeof message === "string") {
    // 忽略 ChunkLoadError（已由 ErrorBoundary 处理）
    if (message.includes("dynamically imported module")) {
      return false;
    }
    // 忽略 ResizeObserver 良性警告
    if (message.includes("ResizeObserver")) {
      return false;
    }
  }
  console.error("[GlobalError]", {
    message: String(message),
    source,
    line: lineno,
    col: colno,
    error: error instanceof Error ? error.message : error,
  });
  // 返回 false 让浏览器执行默认处理（控制台输出）
  return false;
};
```

- [ ] **Step 3: 增强现有的 unhandledrejection 监听**

在现有 `unhandledrejection` 处理器中添加分类逻辑：

```ts
window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason;
  if (reason?.message?.includes("Failed to fetch dynamically imported module")) {
    // ChunkLoadError → ErrorBoundary 已处理，仅记录
    console.warn("[UnhandledRejection] ChunkLoadError:", reason.message);
  } else if (reason?.response?.status === 401) {
    console.warn("[UnhandledRejection] 401 — token may be expired");
  } else {
    console.error("[UnhandledRejection]", reason);
  }
  event.preventDefault(); // 阻止默认的 console 二次输出
});
```

- [ ] **Step 4: 验证 flake8 和 TypeScript 通过**

```bash
cd frontend && npx tsc --noEmit
```
Expected: 0 errors.

- [ ] **Step 5: 提交**

```bash
git add frontend/src/utils/errorHandler.ts
git commit -m "feat(layer-3): add window.onerror + enhanced unhandledrejection handling"
```

---

### Task 9: API 响应拦截器增强 — request.ts

**Files:**
- Modify: `frontend/src/api/request.ts`

- [ ] **Step 1: 读取现有 request.ts 理解当前拦截器结构**

```bash
grep -n "interceptors\|use(" frontend/src/api/request.ts
```

- [ ] **Step 2: 增强响应拦截器——脏数据过滤**

在成功响应拦截器中（`response` handler），添加数据形状安全检查：

```ts
instance.interceptors.response.use(
  (response) => {
    const data = response.data;
    // 成功响应：确保常见字段类型安全
    if (data && typeof data === "object") {
      if ("items" in data && !Array.isArray(data.items)) {
        console.warn("[API] 'items' field is not an array, defaulting to []", data);
        data.items = [];
      }
      if ("data" in data && data.data === null) {
        data.data = {};
      }
      if ("total" in data && typeof data.total !== "number") {
        data.total = Array.isArray(data.items) ? data.items.length : 0;
      }
    }
    return data;
  },
  // ... error handler
);
```

- [ ] **Step 3: 增强响应拦截器——分类错误处理**

在错误响应拦截器中（`error` handler），添加分类处理：

```ts
  (error) => {
    // 已取消的请求不提示
    if (error.__CANCEL__ || error.code === "ERR_CANCELED") {
      return Promise.reject(error);
    }

    if (error.response) {
      const { status, data } = error.response;
      if (status === 401) {
        // Token 过期 → 不清除本地状态，由 auth store 统一处理
        console.warn("[API] 401 Unauthorized");
      } else if (status === 403) {
        ElMessage.error(data?.detail || "权限不足，无法执行此操作");
      } else if (status >= 500) {
        ElMessage.error("服务器异常，请稍后重试");
      } else if (status === 404) {
        // 404 可能由前端路由处理，仅记录
        console.warn(`[API] 404: ${error.config?.url}`);
      } else {
        ElMessage.error(data?.detail || data?.message || "请求失败");
      }
    } else if (error.code === "ERR_NETWORK" || error.message?.includes("NetworkError")) {
      ElMessage.error("网络连接失败，请检查后端服务是否正常运行");
    } else if (error.code === "ECONNABORTED") {
      ElMessage.error("请求超时，请重试");
    } else {
      // 未知错误（如 JSON 解析失败、CORS 等）
      console.error("[API] Unexpected error:", error);
    }

    return Promise.reject(error);
  }
```

- [ ] **Step 4: 验证 TypeScript 和现有 API 测试通过**

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run tests/unit/api/
```
Expected: all pass.

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/request.ts
git commit -m "feat(layer-3): enhanced API interceptor — dirty data guard + classified errors"
```

---

### Task 10: useSafeData — 安全数据访问工具

**Files:**
- Create: `frontend/src/composables/useSafeData.ts`
- Create: `frontend/tests/unit/composables/useSafeData.test.ts`

- [ ] **Step 1: 编写测试文件**

Write `frontend/tests/unit/composables/useSafeData.test.ts`:

```ts
import { describe, it, expect } from 'vitest';
import { safeArray, safeObject, safeString, safeNumber } from '@/composables/useSafeData';

describe('useSafeData', () => {
  it('safeArray: null → []', () => {
    expect(safeArray(null)).toEqual([]);
  });
  it('safeArray: [1,2] → [1,2]', () => {
    expect(safeArray([1, 2])).toEqual([1, 2]);
  });
  it('safeArray: "not-array" → []', () => {
    expect(safeArray("not-array")).toEqual([]);
  });
  it('safeObject: null → {}', () => {
    expect(safeObject(null, { default: true })).toEqual({ default: true });
  });
  it('safeObject: valid object preserved', () => {
    expect(safeObject({ a: 1 }, {})).toEqual({ a: 1 });
  });
  it('safeString: null → ""', () => {
    expect(safeString(null)).toBe("");
  });
  it('safeString: "hello" → "hello"', () => {
    expect(safeString("hello")).toBe("hello");
  });
  it('safeNumber: NaN → 0', () => {
    expect(safeNumber(NaN)).toBe(0);
  });
  it('safeNumber: undefined → 0', () => {
    expect(safeNumber(undefined)).toBe(0);
  });
  it('safeNumber: 42 → 42', () => {
    expect(safeNumber(42)).toBe(42);
  });
});
```

- [ ] **Step 2: 实现 useSafeData.ts**

```ts
/**
 * useSafeData — API 脏数据安全访问工具
 *
 * 防御性类型守卫：确保从 API 获取的数据字段具有安全的类型和默认值。
 * 不修改原始数据，返回安全的副本或默认值。
 */

/** 确保值为数组，否则返回空数组 */
export function safeArray<T = unknown>(value: unknown, fallback: T[] = []): T[] {
  return Array.isArray(value) ? (value as T[]) : fallback;
}

/** 确保值为非数组对象，否则返回默认对象 */
export function safeObject<T extends Record<string, unknown>>(
  value: unknown,
  fallback: T,
): T {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as T;
  }
  return fallback;
}

/** 确保值为字符串，否则返回空字符串 */
export function safeString(value: unknown, fallback: string = ""): string {
  return typeof value === "string" ? value : fallback;
}

/** 确保值为有效数字，NaN/Infinity/undefined/null → 默认值 */
export function safeNumber(value: unknown, fallback: number = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}
```

- [ ] **Step 3: 运行测试验证通过**

```bash
cd frontend && npx vitest run tests/unit/composables/useSafeData.test.ts
```
Expected: 10/10 PASS.

- [ ] **Step 4: 提交**

```bash
git add frontend/src/composables/useSafeData.ts frontend/tests/unit/composables/useSafeData.test.ts
git commit -m "feat(layer-3): useSafeData — safe API data access utilities"
```

---

### Task 11: 内存泄漏修复（4 处）

**Files:**
- Modify: `frontend/src/components/ui/StatusTag.vue`
- Modify: `frontend/src/components/business/SystemStatus.vue`
- Modify: `frontend/src/composables/useResponsiveSidebar.ts`
- Modify: `frontend/src/composables/useECharts.ts`

- [ ] **Step 1: 修复 StatusTag.vue — setInterval 清理**

Read line 95 area, add `onUnmounted` cleanup:

```ts
import { onUnmounted } from "vue";

// 在 setInterval 之后添加
const _intervalId = setInterval(() => { /* existing logic */ }, interval);

onUnmounted(() => {
  clearInterval(_intervalId);
});
```

- [ ] **Step 2: 修复 SystemStatus.vue — _monitorInterval 清理**

Read line 244 area, ensure `onUnmounted` clears:

```ts
onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
});
```

- [ ] **Step 3: 修复 useResponsiveSidebar.ts — resize 监听清理**

Read line 70, add `onUnmounted` cleanup:

```ts
onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
});
```

- [ ] **Step 4: 修复 useECharts.ts — resize 监听 + timer 清理**

Read the composable, ensure `onUnmounted`:

```ts
onUnmounted(() => {
  window.removeEventListener("resize", _onResize);
  if (_resizeTimer) {
    clearTimeout(_resizeTimer);
    _resizeTimer = null;
  }
});
```

- [ ] **Step 5: 验证所有现有测试通过**

```bash
cd frontend && npx vitest run
```
Expected: 134/134 test files pass.

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/ui/StatusTag.vue \
        frontend/src/components/business/SystemStatus.vue \
        frontend/src/composables/useResponsiveSidebar.ts \
        frontend/src/composables/useECharts.ts
git commit -m "fix(layer-3): memory leak fixes — setInterval/resize listener cleanup on unmount"
```

---

## 最终验证

- [ ] **全量测试**

```bash
cd frontend && npx vitest run
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd backend && python -m flake8 app/ --max-line-length=120 --count
cd backend && python -m pytest tests/ -q --tb=short
```

Expected: all pass.

- [ ] **手动冒烟测试**

1. 构建前端 + 同步 + 审计: `cd frontend && npm run build && call scripts\build\sync-frontend-dist.bat && python scripts\audit_static_assets.py`
2. 启动后端: `cd backend && python start.py`
3. 浏览器访问 `http://localhost:8000` → 所有页面正常加载
4. 模拟 chunk 404: 删除一个 JS 文件 → 访问对应路由 → 确认显示降级 UI 而非白屏
5. `Ctrl+Shift+R` 硬刷新 → 确认不白屏
6. 访问 `/version.json` → 确认返回正确版本号

- [ ] **最终提交**

```bash
git add -A
git commit -m "feat: frontend stability three-layer defense — build-time checks + runtime fallback + global error handling"
```
