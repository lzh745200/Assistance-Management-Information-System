<template>
  <div class="policy-detail">
    <el-card v-loading="loading">
      <template #header
        ><span>{{ policy?.title || '政策详情' }}</span></template
      >
      <el-descriptions v-if="policy" :column="2" border>
        <el-descriptions-item label="标题">{{ policy.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ policy.category }}</el-descriptions-item>
        <el-descriptions-item label="级别">{{ policy.level }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ policy.status }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const policy = ref<any>(null)
const loading = ref(false)
onMounted(async () => {
  const id = route.params.id
  if (id) {
    loading.value = true
    try {
      /* fetch */
    } finally {
      loading.value = false
    }
  }
})
</script>
