<template><BaseChart :option="chartOption" :height="height" /></template>
<script setup lang="ts">
import { computed } from "vue";
import BaseChart from "./BaseChart.vue";
const p = defineProps<{
  data: { name: string; value: number }[];
  height?: number;
}>();
const chartOption = computed(() => ({
  xAxis: { type: "category", data: (p.data || []).map((d) => d.name) },
  yAxis: { type: "value" },
  series: [
    { type: "line", data: (p.data || []).map((d) => d.value), smooth: true },
  ],
}));
</script>
