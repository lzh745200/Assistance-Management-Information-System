<template>
  <el-empty :description="text || '暂无数据'" :image-size="size" />
</template>
<script setup lang="ts">
defineProps<{ text?: string; size?: number }>();
</script>
