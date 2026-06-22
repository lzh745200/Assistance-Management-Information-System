<template>
  <el-card class="project-card"
    ><template #header
      ><span>{{ title || name }}</span></template
    ><el-progress v-if="progress != null" :percentage="progress" />
    <p>{{ description }}</p></el-card
  >
</template>
<script setup lang="ts">
defineProps<{
  title?: string
  name?: string
  description?: string
  progress?: number
  status?: string
}>()
</script>
