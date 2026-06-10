<template>
  <el-card class="village-card"
    ><template #header
      ><span>{{ name }}</span></template
    >
    <p>{{ province }} {{ county }}</p>
    <el-tag v-if="isRevitalizationTier">振兴梯队</el-tag></el-card
  >
</template>
<script setup lang="ts">
defineProps<{
  name?: string;
  province?: string;
  county?: string;
  tier?: string;
  isRevitalizationTier?: boolean;
}>();
</script>
