<template>
  <div class="project-detail">
    <h2>项目详情</h2>
    <p v-if="loading">加载中...</p>
    <div v-else-if="project">
      <p>项目名称: {{ project.name }}</p>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { projectsApi } from "@/api/projects";
import { safeRouteParam } from "@/composables/useRouterSafe";
const route = useRoute();
const loading = ref(true);
const project = ref(null);
onMounted(async () => {
  try {
    project.value = await projectsApi.get(safeRouteParam(route.params.id));
  } catch (e) {
    console.error("加载项目详情失败:", e);
    ElMessage.error("项目详情加载失败，请返回重试");
  } finally {
    loading.value = false;
  }
});
</script>
