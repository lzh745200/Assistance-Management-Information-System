<template>
  <div class="dashboard-home">
    <PageHeader @toggle-layout="showLayoutEditor = !showLayoutEditor" />
    <div v-if="showLayoutEditor" class="layout-editor-banner">
      自定义布局面板已从主页移至此处（原 HomeSafe 布局编辑器功能保留）
    </div>
    <KpiCards />
    <ChartRow />
    <InfoRow />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import PageHeader from "./PageHeader.vue";
import KpiCards from "./KpiCards.vue";
import ChartRow from "./ChartRow.vue";
import InfoRow from "./InfoRow.vue";

const showLayoutEditor = ref(false);
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
