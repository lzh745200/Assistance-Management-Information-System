<template>
  <div class="help-center">
    <el-card class="page-header">
      <div class="header-content">
        <h2>帮助中心</h2>
        <p class="description">查看系统使用帮助和常见问题</p>
      </div>
    </el-card>

    <el-card class="help-content">
      <iframe
        :src="helpUrl"
        frameborder="0"
        class="help-iframe"
        @load="handleLoad"
      ></iframe>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";

const helpUrl = ref("/docs/help/index.html");
const loading = ref(true);

const handleLoad = () => {
  loading.value = false;
};

onMounted(() => {
  // 可以根据路由参数加载不同的帮助页面
  const hash = window.location.hash;
  if (hash) {
    helpUrl.value = `/docs/help/index.html${hash}`;
  }
});
</script>

<style scoped lang="scss">
.help-center {
  padding: 20px;
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
  flex-shrink: 0;

  .header-content {
    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      color: #303133;
    }

    .description {
      margin: 0;
      color: #909399;
      font-size: 14px;
    }
  }
}

.help-content {
  flex: 1;
  overflow: hidden;
  padding: 0;

  .help-iframe {
    width: 100%;
    height: 100%;
    border: none;
  }
}
</style>
