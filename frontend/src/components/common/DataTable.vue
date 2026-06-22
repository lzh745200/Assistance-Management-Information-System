<template>
  <div>
    <el-table :data="data" :loading="loading" border stripe
      ><el-table-column
        v-for="col in columns"
        :key="col.key"
        :prop="col.key"
        :label="col.label"
        :width="col.width"
    /></el-table>
  </div>
</template>
<script setup lang="ts">
defineProps<{
  data: any[]
  columns: { key: string; label: string; width?: number }[]
  loading?: boolean
}>()
</script>
