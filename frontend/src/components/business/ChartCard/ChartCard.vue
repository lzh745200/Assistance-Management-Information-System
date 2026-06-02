<template>
  <el-card class="chart-card"
    ><template #header
      ><span>{{ title }}</span></template
    >
    <div :style="{ height: (height || 300) + 'px' }"><slot /></div
  ></el-card>
</template>
<script setup lang="ts">
defineProps<{ title?: string; height?: number }>();
</script>
