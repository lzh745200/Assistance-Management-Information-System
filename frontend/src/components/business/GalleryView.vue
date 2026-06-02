<template>
  <div class="gallery-view">
    <el-empty v-if="!images?.length" description="暂无图片" /><el-row
      v-else
      :gutter="8"
      ><el-col v-for="(img, i) in images" :key="i" :span="6"
        ><el-image :src="img" fit="cover" /></el-col
    ></el-row>
  </div>
</template>
<script setup lang="ts">
defineProps<{ images?: string[]; cols?: number }>();
</script>
