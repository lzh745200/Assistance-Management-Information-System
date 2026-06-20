<template>
  <div class="skeleton-list" role="status" aria-label="加载中">
    <el-skeleton :rows="rows" :animated="animated" :throttle="500">
      <template v-if="showHeader" #template>
        <div class="skeleton-header">
          <el-skeleton-item
            v-for="i in columns"
            :key="i"
            variant="text"
            style="width: 100%"
          />
        </div>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    rows?: number;
    columns?: number;
    animated?: boolean;
    showHeader?: boolean;
  }>(),
  {
    rows: 5,
    columns: 4,
    animated: true,
    showHeader: true,
  },
);
</script>

<style scoped>
.skeleton-list {
  padding: 16px;
}
.skeleton-header {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}
</style>
