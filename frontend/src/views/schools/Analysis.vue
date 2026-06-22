<template>
  <div class="school-analysis">
    <el-card>
      <template #header><span>学校分析</span></template>
      <el-row :gutter="16">
        <el-col :span="12"><BaseChart :option="typeOption" height="350" /></el-col>
        <el-col :span="12"><BaseChart :option="regionOption" height="350" /></el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from '@/components/common/BaseChart.vue'

const typeOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{ type: 'pie', data: [], radius: ['40%', '70%'] }],
}))

const regionOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: [] }],
}))
</script>
