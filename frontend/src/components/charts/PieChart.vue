<template><BaseChart :option="chartOption" :height="height" /></template>
<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
const p = defineProps<{
  data: { name: string; value: number }[]
  height?: number
}>()
const chartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{ type: 'pie', data: p.data || [], radius: ['40%', '70%'] }],
}))
</script>
