<template>
  <div
    ref="chartRef"
    class="base-chart"
    :style="{ width: width, height: height }"
  ></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
import echarts from "@/utils/echarts";

interface Props {
  option: echarts.EChartsCoreOption;
  width?: string;
  height?: string;
  theme?: string;
  autoResize?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  width: "100%",
  height: "400px",
  theme: "",
  autoResize: true,
});

const emit = defineEmits<{
  "chart-ready": [chart: echarts.ECharts];
  "chart-click": [params: any];
}>();

const chartRef = ref<HTMLDivElement>();
let chartInstance: echarts.ECharts | null = null;

const initChart = () => {
  if (!chartRef.value) return;

  chartInstance = echarts.init(chartRef.value, props.theme);
  chartInstance.setOption(props.option);

  chartInstance.on("click", (params) => {
    emit("chart-click", params);
  });

  emit("chart-ready", chartInstance);
};

const resizeChart = () => {
  chartInstance?.resize();
};

watch(
  () => props.option,
  (newOption) => {
    if (chartInstance) {
      chartInstance.setOption(newOption, true);
    }
  },
  { deep: true },
);

onMounted(() => {
  nextTick(() => {
    initChart();

    if (props.autoResize) {
      window.addEventListener("resize", resizeChart);
    }
  });
});

onUnmounted(() => {
  if (props.autoResize) {
    window.removeEventListener("resize", resizeChart);
  }

  chartInstance?.dispose();
  chartInstance = null;
});

defineExpose({
  getChart: () => chartInstance,
  resize: resizeChart,
});
</script>

<style scoped>
.base-chart {
  min-height: 200px;
}
</style>
