<template>
  <el-card class="industry-card"
    ><template #header
      ><span>{{ title || name }}</span></template
    >
    <p>{{ description }}</p></el-card
  >
</template>
<script setup lang="ts">
defineProps<{
  title?: string;
  name?: string;
  description?: string;
  industry?: string;
}>();
</script>
