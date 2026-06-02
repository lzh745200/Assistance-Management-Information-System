<template>
  <el-card class="statistics-card"
    ><el-statistic
      :title="title"
      :value="value"
      :prefix="prefix"
      :suffix="suffix"
  /></el-card>
</template>
<script setup lang="ts">
defineProps<{
  title?: string;
  value?: number;
  prefix?: string;
  suffix?: string;
}>();
</script>
