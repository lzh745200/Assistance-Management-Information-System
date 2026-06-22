<template>
  <el-button :loading="loading" @click="$emit('import')">导入</el-button>
</template>
<script setup lang="ts">
defineProps<{ loading?: boolean }>()
defineEmits<{ (e: 'import'): void }>()
</script>
