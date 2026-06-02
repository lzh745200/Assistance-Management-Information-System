<template>
  <el-table :data="data" :loading="loading" border stripe><slot /></el-table>
</template>
<script setup lang="ts">
defineProps<{ data: any[]; loading?: boolean }>();
</script>
