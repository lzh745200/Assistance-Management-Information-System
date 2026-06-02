<template>
  <div ref="chartRef" :style="{ height: height + 'px' }"></div>
</template>
<script setup lang="ts">
import { ref, onMounted } from "vue";
defineProps<{ height?: number; type?: string }>();
const chartRef = ref();
onMounted(async () => {
  if (chartRef.value) {
    const e = await import("echarts");
    e.init(chartRef.value);
  }
});
</script>
