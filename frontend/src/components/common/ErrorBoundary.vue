<template>
  <div>
    <slot v-if="!hasError" />
    <el-result
      v-else
      icon="error"
      title="组件加载失败"
      :sub-title="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="retry">重试</el-button>
        <el-button @click="hasError = false">忽略</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from "vue";

const hasError = ref(false);
const errorMessage = ref("请刷新页面重试");

onErrorCaptured((err: Error, _instance, _info) => {
  hasError.value = true;
  errorMessage.value = err?.message || "未知错误，请刷新页面重试";
  console.error("[ErrorBoundary]", err);
  // 返回 false 阻止错误继续向上传播
  return false;
});

function retry() {
  hasError.value = false;
  errorMessage.value = "请刷新页面重试";
}
</script>
