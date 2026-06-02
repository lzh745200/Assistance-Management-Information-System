<template>
  <el-button :loading="loading" @click="$emit('export')">导出</el-button>
</template>
<script setup lang="ts">
defineProps<{ loading?: boolean }>();
defineEmits<{ (e: "export"): void }>();
</script>
