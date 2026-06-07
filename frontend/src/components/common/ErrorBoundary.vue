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
