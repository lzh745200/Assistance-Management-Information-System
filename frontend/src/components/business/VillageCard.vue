<template>
  <el-card class="village-card"
    ><template #header
      ><span>{{ name }}</span></template
    >
    <p>{{ province }} {{ county }}</p>
    <el-tag>{{ tier || revitalization_tier }}</el-tag></el-card
  >
</template>
<script setup lang="ts">
defineProps<{
  name?: string;
  province?: string;
  county?: string;
  tier?: string;
  revitalization_tier?: string;
}>();
</script>
