<template>
  <div class="personnel-list">
    <el-empty v-if="!items?.length" description="无人员数据" /><el-table v-else :data="items"
      ><el-table-column prop="name" label="姓名" /><el-table-column
        prop="role"
        label="职务" /><el-table-column prop="organization" label="单位"
    /></el-table>
  </div>
</template>
<script setup lang="ts">
defineProps<{ items?: any[] }>()
</script>
