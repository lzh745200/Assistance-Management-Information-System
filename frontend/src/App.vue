<template>
  <el-config-provider :locale="zhCn" :size="'default'">
    <router-view v-slot="{ Component }">
      <template v-if="appError">
        <div class="app-error-boundary">
          <div class="error-content">
            <h1>页面异常</h1>
            <p>{{ errorMessage }}</p>
            <button class="refresh-btn" @click="handleRetry">重试</button>
          </div>
        </div>
      </template>
      <component :is="Component" v-else />
    </router-view>
  </el-config-provider>
</template>

<script setup lang="ts">
/**
 * 帮扶管理信息系统 - 根组件
 *
 * 职责：
 * 1. 提供 Element Plus 全局配置
 * 2. 路由容器 + 错误边界（组件级，切换路由自动恢复）
 */
import zhCn from "element-plus/es/locale/lang/zh-cn";
import { onErrorCaptured, ref } from "vue";
import { useRouter } from "vue-router";

document.title = "帮扶管理信息系统";

const router = useRouter();
const appError = ref(false);
const errorMessage = ref("请重试或返回首页");

onErrorCaptured((err, _instance, info) => {
  console.error("[App] 组件错误:", info, err);
  appError.value = true;
  const msg = (err as any)?.message || String(err);
  errorMessage.value = msg.length > 80 ? msg.slice(0, 80) + "…" : msg;
  return false; // 阻止错误继续传播导致白屏
});

// 路由切换时自动清除错误状态
router.afterEach(() => {
  if (appError.value) appError.value = false;
});

function handleRetry() {
  appError.value = false;
}
</script>

<style>
/* === 全部提示/通知强制页面居中（必须全局，EP 可能 teleport 到 body） === */
.el-message {
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
}
.el-notification {
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  margin: 0 !important;
}
.el-notification__group {
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* 全局基础样式 */
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
  font-family:
    "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Helvetica, Arial,
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 错误边界回退UI */
.app-error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #081c15;
  color: #fff;
  text-align: center;
}

.error-content h1 {
  font-size: 28px;
  color: #d4af37;
  margin-bottom: 12px;
}

.error-content p {
  font-size: 16px;
  color: #a8dadc;
  margin-bottom: 24px;
}

.refresh-btn {
  padding: 12px 32px;
  background: linear-gradient(135deg, #d4af37, #c9a227);
  color: #081c15;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
}
</style>
