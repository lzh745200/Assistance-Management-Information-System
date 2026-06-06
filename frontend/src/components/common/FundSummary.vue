<template>
  <div class="fund-summary">
    <el-row :gutter="16">
      <el-col v-for="item in items" :key="item.key" :xs="12" :sm="6">
        <el-card shadow="hover" class="fund-summary__card">
          <el-statistic :title="item.label" :value="item.value">
            <template v-if="item.prefix" #prefix>{{ item.prefix }}</template>
            <template v-if="item.suffix" #suffix>{{ item.suffix }}</template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  data: Record<string, any>;
}>();

const items = computed(() => [
  {
    key: "total_amount",
    label: "经费总额",
    value: props.data?.total_amount ?? 0,
    prefix: "¥",
  },
  {
    key: "approved_amount",
    label: "已批准",
    value: props.data?.approved_amount ?? 0,
    prefix: "¥",
  },
  {
    key: "pending_amount",
    label: "待审批",
    value: props.data?.pending_amount ?? 0,
    prefix: "¥",
  },
  {
    key: "total_count",
    label: "记录总数",
    value: props.data?.total_count ?? 0,
    suffix: "条",
  },
]);
</script>

<style scoped>
.fund-summary {
  margin-bottom: 16px;
}
.fund-summary__card {
  text-align: center;
}
</style>
