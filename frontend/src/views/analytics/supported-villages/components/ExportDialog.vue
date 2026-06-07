<template>
  <el-dialog
    :model-value="modelValue"
    title="导出帮扶村数据"
    width="500px"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-form :model="exportForm" label-width="100px">
      <el-form-item label="导出年份" required>
        <el-select
          v-model="exportForm.year"
          placeholder="请选择年份"
          style="width: 100%"
        >
          <el-option
            v-for="year in availableYears"
            :key="year"
            :label="`${year}年`"
            :value="year"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="导出格式" required>
        <el-radio-group v-model="exportForm.format">
          <el-radio value="excel">Excel (.xlsx)</el-radio>
          <el-radio value="pdf">PDF</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="数据范围">
        <el-checkbox-group v-model="exportForm.includeSections">
          <el-checkbox value="population">人口数据</el-checkbox>
          <el-checkbox value="income">收入数据</el-checkbox>
          <el-checkbox value="industry">产业帮扶</el-checkbox>
          <el-checkbox value="infrastructure">基础设施</el-checkbox>
          <el-checkbox value="education">教育帮扶</el-checkbox>
          <el-checkbox value="medical">医疗帮扶</el-checkbox>
          <el-checkbox value="consumption">消费帮扶</el-checkbox>
          <el-checkbox value="employment">就业帮扶</el-checkbox>
          <el-checkbox value="partyBuilding">党建帮扶</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="exporting" @click="handleExport">
        导出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
// @ts-nocheck
import { logger } from "@/utils/logger";

import { ref, reactive } from "vue";
import { ElMessage } from "element-plus";
import { exportAndDownloadExcel, exportAndDownloadPdf } from "@/api/report";
import type { ExportFormat, DataSection } from "@/types/analytics";

defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  export: [];
}>();

const currentYear = new Date().getFullYear();
const availableYears = Array.from({ length: 6 }, (_, i) => currentYear - i + 1);

const exporting = ref(false);

const exportForm = reactive({
  year: currentYear,
  format: "excel" as ExportFormat,
  includeSections: [
    "population",
    "income",
    "industry",
    "infrastructure",
    "education",
  ] as DataSection[],
});

const handleExport = async () => {
  if (!exportForm.year) {
    ElMessage.warning("请选择导出年份");
    return;
  }

  exporting.value = true;
  try {
    const query = {
      year: exportForm.year,
      format: exportForm.format,
      includeSections: exportForm.includeSections,
    };

    if (exportForm.format === "excel") {
      await exportAndDownloadExcel(query);
    } else {
      await exportAndDownloadPdf(query);
    }

    ElMessage.success("导出成功");
    emit("export");
    emit("update:modelValue", false);
  } catch (error) {
    logger.error("导出失败:", error);
    ElMessage.error("导出失败，请稍后重试");
  } finally {
    exporting.value = false;
  }
};
</script>

<style scoped>
:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}
</style>
