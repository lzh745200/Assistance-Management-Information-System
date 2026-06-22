<template>
  <el-tree
    :data="data"
    :props="{ label: 'name', children: 'children' }"
    node-key="id"
    default-expand-all
  />
</template>
<script setup lang="ts">
defineProps<{ data: any[] }>()
</script>
