<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    width="80%"
    :before-close="handleClose"
    @update:model-value="handleUpdateVisible"
  >
    <div ref="printContent" class="print-content">
      <div class="print-header">
        <h2>{{ title }}</h2>
        <div class="print-info">
          <p>打印时间: {{ printTime }}</p>
          <p>打印人: {{ printer }}</p>
        </div>
      </div>

      <el-table :data="data" border style="width: 100%" :show-header="true">
        <el-table-column
          v-for="column in columns"
          :key="column.key"
          :prop="column.key"
          :label="column.label"
          min-width="120"
        />
      </el-table>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="handlePrint">打印</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import { escapeHtml, sanitizeHtml } from "@/utils/sanitize";

interface Column {
  key: string;
  label: string;
}

interface Props {
  data: any[];
  columns: Column[];
  title: string;
  visible: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(["close", "update:visible"]);

const authStore = useAuthStore();
const printContent = ref<HTMLElement>();

const printTime = computed(() => {
  return new Date().toLocaleString("zh-CN");
});

const printer = computed(() => {
  return authStore.user?.username || "未知用户";
});

const handleUpdateVisible = (value: boolean) => {
  emit("update:visible", value);
  if (!value) {
    emit("close");
  }
};

const handleClose = () => {
  emit("update:visible", false);
  emit("close");
};

const handlePrint = () => {
  if (!printContent.value) return;

  const printWindow = window.open("", "_blank");
  if (!printWindow) return;

  // Escape title to prevent XSS
  const safeTitle = escapeHtml(props.title);

  const styles = `
    <style>
      body { 
        font-family: 'Microsoft YaHei', Arial, sans-serif; 
        margin: 20px;
        color: #000;
        font-size: 12px;
      }
      .print-table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-bottom: 20px;
      }
      .print-table th, 
      .print-table td { 
        border: 1px solid #000; 
        padding: 6px 8px; 
        text-align: left;
      }
      .print-table th { 
        background-color: #f0f0f0; 
        font-weight: bold;
      }
      .print-header { 
        text-align: center; 
        margin-bottom: 20px;
        border-bottom: 2px solid #000;
        padding-bottom: 10px;
      }
      .print-header h2 { 
        margin: 0 0 10px; 
        font-size: 18px;
      }
      .print-info { 
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #666;
      }
      @media print {
        body { margin: 0; }
        .no-print { display: none; }
      }
    </style>
  `;

  const tableHtml = sanitizeHtml(printContent.value.innerHTML);

  printWindow.document.write(`
    <html>
      <head>
        <title>${safeTitle}</title>
        ${styles}
      </head>
      <body>
        ${tableHtml}
        <script>
          window.onload = function() {
            window.print();
            window.onafterprint = function() {
              window.close();
            };
          };
        ${"<"}/script>
      </body>
    </html>
  `);
  printWindow.document.close();
};
</script>

<style scoped>
.print-content {
  max-height: 60vh;
  overflow-y: auto;
}

.print-header {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e8e8e8;
}

.print-header h2 {
  margin: 0 0 8px;
  color: #303133;
}

.print-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
}

.print-info p {
  margin: 0;
}
</style>
