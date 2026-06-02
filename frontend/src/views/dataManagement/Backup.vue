<template>
  <div class="backup-page">
    <div class="page-header">
      <h2 class="page-title">数据备份管理</h2>
      <p class="page-desc">管理系统数据备份，支持创建、恢复、验证和清理操作</p>
    </div>
    <BackupSection @backup-complete="handleBackupComplete" />
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import BackupSection from "./components/BackupSection.vue";

function handleBackupComplete() {
  ElMessage.success("备份操作完成");
}
</script>

<style scoped>
.backup-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
  margin: 0 0 4px;
}
.page-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}
</style>
