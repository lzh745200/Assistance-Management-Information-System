<template>
  <div>
    <el-table :data="data" :loading="loading" border stripe
      ><el-table-column
        v-for="col in columns"
        :key="col.key"
        :prop="col.key"
        :label="col.label"
        :width="col.width" /></el-table
    ><el-pagination
      v-if="pagination"
      v-model:current-page="page"
      :total="total"
      :page-size="pageSize"
      @current-change="$emit('page-change', $event)"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
defineProps<{
  data: any[];
  columns: { key: string; label: string; width?: number }[];
  loading?: boolean;
  pagination?: boolean;
  total?: number;
  pageSize?: number;
}>();
defineEmits<{ (e: "page-change", page: number): void }>();
const page = ref(1);
</script>
