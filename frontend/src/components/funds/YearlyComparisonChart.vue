<template>
  <el-card class="chart-card">
    <template #header><span class="title">年度对比</span></template>
    <BaseChart v-if="chartOption" :option="chartOption" height="320px" />
    <el-empty v-else description="暂无年度对比数据" />
  </el-card>
</template>
<script setup lang="ts">
import { ref, computed, watch } from "vue";
import BaseChart from "@/components/common/BaseChart.vue";
import { get } from "@/api/request";
import type { EChartsOption } from "echarts";

const props = defineProps<{
  yearStart?: number;
  yearEnd?: number;
  department?: string;
}>();

const yearlyData = ref<any[]>([]);

async function load() {
  try {
    const params: any = {};
    if (props.yearStart) params.year_start = props.yearStart;
    if (props.yearEnd) params.year_end = props.yearEnd;
    if (props.department) params.department = props.department;
    const res: any = await get("/funds/supported-village/statistics/yearly-comparison", params);
    yearlyData.value = res?.data || res || [];
  } catch {
    yearlyData.value = [];
  }
}

const chartOption = computed<EChartsOption | null>(() => {
  if (!yearlyData.value.length) return null;
  const years = yearlyData.value.map((d: any) => String(d.year || ""));
  const amounts = yearlyData.value.map((d: any) => Number(d.total_actual || d.amount || 0));
  return {
    tooltip: { trigger: "axis" },
    legend: { data: ["经费总额"] },
    xAxis: { type: "category", data: years },
    yAxis: { type: "value", name: "万元" },
    series: [{
      name: "经费总额", type: "bar", data: amounts,
      itemStyle: { color: "#40916c" },
    }],
  };
});

watch(() => [props.yearStart, props.yearEnd, props.department], load, { immediate: true });

defineExpose({ refresh: load });
</script>
