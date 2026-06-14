<template>
  <div class="dashboard-home">
    <PageHeader @toggle-layout="showLayoutEditor = !showLayoutEditor" />
    <div v-if="showLayoutEditor" class="layout-editor-banner">
      自定义布局面板已从主页移至此处（原 HomeSafe 布局编辑器功能保留）
    </div>
    <KpiCards />
    <QuickActions
      :is-manager="isManager"
      :is-admin="isAdmin"
      :backing-up="false"
      @backup="handleBackup"
      @restore="handleRestore"
    />
    <ChartRow />
    <InfoRow />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import PageHeader from "./PageHeader.vue";
import KpiCards from "./KpiCards.vue";
import QuickActions from "./components/QuickActions.vue";
import ChartRow from "./ChartRow.vue";
import InfoRow from "./InfoRow.vue";
import { useUserStore } from "@/stores/user";

const showLayoutEditor = ref(false);
const userStore = useUserStore();
const isAdmin = computed(() => userStore.currentUser?.role === "admin" || userStore.currentUser?.is_superuser);
const isManager = computed(() => isAdmin.value || userStore.currentUser?.role === "manager");

function handleBackup() { ElMessage.info("请前往系统管理→备份管理手动创建备份"); }
function handleRestore() { ElMessage.info("请前往系统管理→备份管理执行恢复"); }
</script>

<style scoped lang="scss">
.dashboard-home {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.layout-editor-banner {
  background: #fef3c7;
  border: 1px dashed #f59e0b;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: #92400e;
}
</style>
