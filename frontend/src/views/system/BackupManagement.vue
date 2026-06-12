<template>
  <div class="backup-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统备份管理</span>
          <el-button type="primary" @click="handleCreateBackup">
            创建备份
          </el-button>
        </div>
      </template>

      <!-- 备份状态 -->
      <el-descriptions :column="3" border class="backup-status">
        <el-descriptions-item label="备份数量">
          {{ backupStatus.backup_count }}
        </el-descriptions-item>
        <el-descriptions-item label="总大小">
          {{ formatSize(backupStatus.total_size) }}
        </el-descriptions-item>
        <el-descriptions-item label="调度器状态">
          <el-tag
            :type="backupStatus.scheduler?.running ? 'success' : 'danger'"
          >
            {{ backupStatus.scheduler?.running ? "运行中" : "已停止" }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 备份列表 -->
      <el-table :data="backupList" style="width: 100%; margin-top: 20px">
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="文件大小">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row.filename ?? row.file_name)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建备份对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建备份" width="500px">
      <el-form :model="backupForm" label-width="120px">
        <el-form-item label="备份描述">
          <el-input
            v-model="backupForm.description"
            placeholder="请输入备份描述"
          />
        </el-form-item>
        <el-form-item label="包含上传文件">
          <el-switch v-model="backupForm.include_uploads" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="confirmCreateBackup"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 恢复备份对话框 -->
    <el-dialog v-model="restoreDialogVisible" title="恢复备份" width="500px">
      <el-upload
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽备份文件到此处，或<em>点击上传</em>
        </div>
      </el-upload>
      <el-alert
        title="警告：恢复备份将覆盖当前所有数据！"
        type="warning"
        :closable="false"
        style="margin-top: 20px"
      />
      <template #footer>
        <el-button @click="restoreDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="loading" @click="confirmRestore">
          确认恢复
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, onMounted } from "vue";
import { ElMessageBox } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import request from "@/api/request";
import { notify as appNotify } from "@/utils/notify";

/** 统一消息通知 — 页面正中显示，3 秒后自动关闭 */
function notify(
  title: string,
  message: string,
  type: "success" | "error" | "warning" | "info" = "success",
) {
  // 使用 appNotify 包装器（已注入全局 showClose + duration），显式覆盖 duration: 3000
  appNotify({
    title,
    message,
    type,
    duration: 3000,
  });
}

const backupList = ref([]);
const backupStatus = ref({
  backup_count: 0,
  total_size: 0,
  scheduler: { running: false },
});
const createDialogVisible = ref(false);
const restoreDialogVisible = ref(false);
const loading = ref(false);
const backupForm = ref({
  description: "手动备份",
  include_uploads: true,
});
const restoreFile = ref<File | null>(null);

// 获取备份列表
const fetchBackupList = async () => {
  try {
    const response = await request.get("/system/backup");
    // 接口返回 {success, data: {items: [...], total: N}}
    const resData = response.data;
    backupList.value = resData?.data?.items ?? resData?.items ?? [];
  } catch (error) {
    notify("错误", "获取备份列表失败", "error");
  }
};

// 获取备份状态（调度器状态）
const fetchBackupStatus = async () => {
  try {
    const response = await request.get("/system/backup/schedule");
    const resData = response.data?.data ?? response.data;
    backupStatus.value = {
      backup_count: backupList.value.length,
      total_size: backupList.value.reduce(
        (sum: number, b: any) => sum + (b.size ?? b.file_size ?? 0),
        0,
      ),
      scheduler: { running: resData?.running ?? resData?.enabled ?? false },
    };
  } catch (error) {
    logger.error("获取备份状态失败:", error);
  }
};

// 创建备份
const handleCreateBackup = () => {
  createDialogVisible.value = true;
};

const confirmCreateBackup = async () => {
  loading.value = true;
  try {
    const response = await request.post("/system/backup", {
      description: backupForm.value.description,
      include_uploads: backupForm.value.include_uploads,
    });

    if (response.data.success !== false) {
      notify("成功", "备份已创建成功", "success");
      createDialogVisible.value = false;
      await fetchBackupList();
      await fetchBackupStatus();
    }
  } catch (error: any) {
    notify("创建失败", error.response?.data?.detail || "创建备份失败", "error");
  } finally {
    loading.value = false;
  }
};

// 删除备份（使用文件名作为路径参数，与后端 DELETE /system/backup/{filename} 对应）
const handleDelete = async (filename: string) => {
  try {
    await ElMessageBox.confirm("确定要删除此备份吗？", "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    const response = await request.delete(`/system/backup/${filename}`);
    if (response.data.success !== false) {
      notify("成功", "备份已删除", "success");
      await fetchBackupList();
      await fetchBackupStatus();
    }
  } catch (error: any) {
    if (error !== "cancel") {
      notify("删除失败", "无法删除备份文件", "error");
    }
  }
};

// 文件选择
const handleFileChange = (file: { raw?: File }) => {
  restoreFile.value = file.raw ?? null;
};

// 恢复备份
const confirmRestore = async () => {
  if (!restoreFile.value) {
    notify("提示", "请先选择备份文件", "warning");
    return;
  }

  loading.value = true;
  try {
    const formData = new FormData();
    formData.append("backup_file", restoreFile.value);

    const response = await request.post(
      "/system/backup/upload-restore",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );

    if (response.data.success) {
      notify("恢复成功", "系统数据已恢复，即将跳转登录页", "success");
      restoreDialogVisible.value = false;
      setTimeout(() => {
        window.location.href = "/login";
      }, 2000);
    }
  } catch (error: any) {
    notify("恢复失败", error.response?.data?.detail || "恢复失败", "error");
  } finally {
    loading.value = false;
  }
};

// 格式化文件大小
const formatSize = (bytes: number) => {
  if (!bytes) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
};

// 格式化时间
const formatTime = (time: string | number | Date) => {
  if (!time) return "-";
  return new Date(time).toLocaleString("zh-CN");
};

onMounted(() => {
  fetchBackupList();
  fetchBackupStatus();
});
</script>

<style scoped>
.backup-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.backup-status {
  margin-bottom: 20px;
}
</style>
