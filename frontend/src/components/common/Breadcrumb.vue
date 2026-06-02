<template>
  <el-breadcrumb
    ><el-breadcrumb-item v-for="(item, i) in items" :key="i" :to="item.to">{{
      item.title
    }}</el-breadcrumb-item></el-breadcrumb
  >
</template>
<script setup lang="ts">
defineProps<{ items: { title: string; to?: string }[] }>();
</script>
