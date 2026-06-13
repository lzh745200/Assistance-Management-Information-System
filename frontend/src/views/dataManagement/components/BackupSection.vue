<template>
  <div class="backup-section">
    <!-- 备份统计 -->
    <el-card class="stats-card">
      <el-row :gutter="20">
        <el-col :span="5">
          <el-statistic title="备份总数" :value="stats.total_backups" />
        </el-col>
        <el-col :span="5">
          <el-statistic
            title="总大小 (MB)"
            :value="stats.total_size"
            :formatter="(v: number) => (v / 1024 / 1024).toFixed(2)"
          />
        </el-col>
        <el-col :span="5">
          <div style="text-align: center">
            <div style="font-size: 12px; color: #909399">自动备份</div>
            <el-tag
              :type="stats.auto_backup_enabled ? 'success' : 'info'"
              size="small"
            >
              {{ stats.auto_backup_enabled ? "已启用" : "未启用" }}
            </el-tag>
          </div>
        </el-col>
        <el-col :span="9">
          <div class="action-buttons">
            <el-button
              type="primary"
              :loading="creating"
              @click="openCreateDialog"
            >
              <el-icon><Plus /></el-icon>
              创建备份
            </el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 定时备份配置 -->
    <el-card class="schedule-card">
      <template #header>
        <div class="card-header">
          <span>定时自动备份</span>
        </div>
      </template>
      <el-form :inline="true" label-width="100px">
        <el-form-item label="启用定时备份">
          <el-switch v-model="scheduleConfig.enabled" @change="saveSchedule" />
        </el-form-item>
        <el-form-item label="备份间隔">
          <el-select
            v-model="scheduleConfig.interval_hours"
            style="width: 140px"
            :disabled="!scheduleConfig.enabled"
          >
            <el-option :label="'每6小时'" :value="6" />
            <el-option :label="'每12小时'" :value="12" />
            <el-option :label="'每天24小时'" :value="24" />
            <el-option :label="'每3天'" :value="72" />
            <el-option :label="'每周'" :value="168" />
          </el-select>
        </el-form-item>
        <el-form-item label="保留份数">
          <el-input-number
            v-model="scheduleConfig.keep_count"
            :min="1"
            :max="50"
            :disabled="!scheduleConfig.enabled"
          />
        </el-form-item>
        <el-form-item label="每日备份时间">
          <el-time-select
            v-model="scheduleConfig.time_of_day"
            start="00:00"
            step="01:00"
            end="23:00"
            :disabled="!scheduleConfig.enabled"
            style="width: 120px"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="savingSchedule"
            :disabled="!scheduleConfig.enabled"
            @click="saveSchedule"
            >保存配置</el-button
          >
        </el-form-item>
      </el-form>
      <div
        v-if="scheduleRunning"
        style="font-size: 13px; color: #67c23a; margin-top: 4px"
      >
        ✓ 定时备份已启动运行中
      </div>
    </el-card>

    <!-- 备份列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>备份列表</span>
          <el-button link @click="loadBackups">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="backups" stripe>
        <el-table-column
          prop="filename"
          label="文件名"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ format.formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          label="描述"
          min-width="150"
          show-overflow-tooltip
        />
        <el-table-column label="压缩" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.compressed ? 'success' : 'info'" size="small">
              {{ row.compressed ? "是" : "否" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button
              size="small"
              :loading="previewing === row.id"
              @click="handlePreview(row as BackupItem)"
            >
              预览
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="handleRestore(row as BackupItem)"
            >
              恢复
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row as BackupItem)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建备份对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建备份" width="500px">
      <el-form label-width="100px">
        <el-form-item label="备份描述">
          <el-input
            v-model="createForm.description"
            placeholder="例如：日常备份"
          />
        </el-form-item>
        <el-form-item label="加密密码">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="留空则不加密"
            show-password
          />
          <div style="font-size: 12px; color: #999; margin-top: 4px">
            设置密码后备份文件将使用 AES-256 加密存储
          </div>
        </el-form-item>
        <el-form-item label="备份内容">
          <el-checkbox v-model="createForm.include_uploads"
            >上传文件(uploads)</el-checkbox
          >
          <el-checkbox v-model="createForm.include_config"
            >配置文件(config)</el-checkbox
          >
          <el-alert
            title="全量备份说明"
            type="info"
            :closable="false"
            style="margin-top: 12px"
          >
            <template #default>
              <div style="font-size: 13px; line-height: 1.5">
                <p style="margin: 0 0 6px">
                  •
                  <strong>数据库：</strong
                  >始终包含所有数据表（帮扶村、项目、学校、经费、用户等）
                </p>
                <p style="margin: 0 0 6px">
                  • <strong>上传文件：</strong>包括用户上传的所有附件和图片
                </p>
                <p style="margin: 0">
                  • <strong>配置文件：</strong>包括系统配置和环境变量
                </p>
              </div>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="creating"
          @click="handleCreateBackup"
          >创建备份</el-button
        >
      </template>
    </el-dialog>

    <!-- 备份内容预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="备份包内容" width="650px">
      <div v-if="previewData.meta.description" style="margin-bottom: 12px">
        <strong>描述：</strong>{{ previewData.meta.description }}
      </div>
      <div
        v-if="previewData.meta.created_at"
        style="margin-bottom: 12px; font-size: 13px; color: #666"
      >
        创建时间：{{ previewData.meta.created_at }} | 包含：{{
          (previewData.meta.contents || []).join(", ")
        }}
      </div>
      <el-table :data="previewData.files" stripe max-height="400">
        <el-table-column
          prop="name"
          label="文件名"
          min-width="250"
          show-overflow-tooltip
        />
        <el-table-column label="原始大小" width="120">
          <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
        </el-table-column>
        <el-table-column label="压缩后" width="120">
          <template #default="{ row }">{{
            row.compressed_size != null
              ? formatFileSize(row.compressed_size)
              : "-"
          }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 恢复确认对话框 -->
    <el-dialog v-model="showRestoreDialog" title="恢复确认" width="550px">
      <el-alert
        title="警告"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        恢复备份将覆盖当前所有数据，此操作不可撤销！恢复后页面将自动刷新。
      </el-alert>
      <div v-if="selectedBackup" class="restore-info">
        <p><strong>备份文件：</strong>{{ selectedBackup.filename }}</p>
        <p>
          <strong>创建时间：</strong
          >{{ format.formatDateTime(selectedBackup.created_at) }}
        </p>
        <p>
          <strong>文件大小：</strong
          >{{ formatFileSize(selectedBackup.file_size) }}
        </p>
      </div>
      <template #footer>
        <el-button @click="showRestoreDialog = false">取消</el-button>
        <el-button type="danger" :loading="restoring" @click="confirmRestore">
          确认恢复
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from "@/utils/logger";

import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Refresh } from "@element-plus/icons-vue";
import request from "@/api/request";
import {
  getBackupList,
  restoreBackup,
  deleteBackup,
  getBackupStats,
  type BackupItem,
  type BackupStats,
} from "@/api/backup";
import { formatFileSize } from "@/api/export";
import { format } from "@/utils";

const emit = defineEmits<{
  (e: "backup-complete"): void;
}>();

// 状态
const loading = ref(false);
const creating = ref(false);
const restoring = ref(false);
const backups = ref<BackupItem[]>([]);
const stats = reactive<BackupStats>({
  total_backups: 0,
  total_size: 0,
  auto_backup_enabled: false,
});
const showRestoreDialog = ref(false);
const selectedBackup = ref<BackupItem | null>(null);

// 定时备份配置
const savingSchedule = ref(false);
const scheduleRunning = ref(false);
const scheduleConfig = reactive({
  enabled: false,
  interval_hours: 24,
  keep_count: 7,
  time_of_day: "02:00",
});

// 加载备份列表
async function loadBackups() {
  loading.value = true;
  try {
    const [listRes, statsRes] = await Promise.all([
      getBackupList(),
      getBackupStats(),
    ]);
    backups.value = listRes.items ?? [];
    Object.assign(stats, statsRes);
  } catch (error) {
    logger.error("加载备份列表失败:", error);
  } finally {
    loading.value = false;
  }
}

// 创建备份对话框
const showCreateDialog = ref(false);
const createForm = reactive({
  description: "",
  include_uploads: true,
  include_config: true,
  password: "",
});

function openCreateDialog() {
  Object.assign(createForm, {
    description: "",
    include_uploads: true,
    include_config: true,
    password: "",
  });
  showCreateDialog.value = true;
}

async function handleCreateBackup() {
  creating.value = true;
  showCreateDialog.value = false;
  try {
    const res: any = await request.post("/system/backup", {
      description: createForm.description || "",
      compress: true,
      include_uploads: createForm.include_uploads,
      include_config: createForm.include_config,
      password: createForm.password || undefined,
    });

    if (res.data.success !== false) {
      ElMessage.success("备份创建成功");
      emit("backup-complete");
      loadBackups();
    } else {
      ElMessage.error(res.data.message || "备份创建失败");
    }
  } catch {
    ElMessage.error("备份创建失败");
  } finally {
    creating.value = false;
  }
}

// 备份内容预览
const showPreviewDialog = ref(false);
const previewData = ref<{
  filename: string;
  size: number;
  files: any[];
  meta: any;
}>({ filename: "", size: 0, files: [], meta: {} });
const previewing = ref<string | number | null | undefined>(null);

async function handlePreview(row: BackupItem) {
  previewing.value = row.id;
  try {
    const res = await request.get(
      `/system/backup/preview/${row.filename || row.id}`,
    );
    previewData.value = res.data;
    showPreviewDialog.value = true;
  } catch {
    ElMessage.error("加载备份预览失败");
  } finally {
    previewing.value = null;
  }
}

// 打开恢复对话框
function handleRestore(row: BackupItem) {
  selectedBackup.value = row;
  showRestoreDialog.value = true;
}

// 确认恢复
async function confirmRestore() {
  if (!selectedBackup.value) return;

  restoring.value = true;
  try {
    const res = await restoreBackup(selectedBackup.value.filename);
    if (res.data.success !== false) {
      ElMessage.success("恢复成功，页面将在 3 秒后刷新");
      showRestoreDialog.value = false;
      emit("backup-complete");
      // 恢复后自动刷新页面
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    } else {
      ElMessage.error(res.data.message || "恢复失败");
    }
  } catch {
    ElMessage.error("恢复失败");
  } finally {
    restoring.value = false;
  }
}

// 删除备份
async function handleDelete(row: BackupItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除备份 "${row.filename}" 吗？`,
      "删除确认",
      { type: "warning" },
    );

    const res = await deleteBackup(row.filename);
    if (res.data.success) {
      ElMessage.success(res.data.message || "删除成功");
      loadBackups();
    } else {
      ElMessage.error(res.data.message || "删除失败");
    }
  } catch {
    // 用户取消
  }
}

async function loadSchedule() {
  try {
    const res = await request.get("/system/backup/schedule");
    const d = res.data;
    scheduleConfig.enabled = d.enabled ?? false;
    scheduleConfig.interval_hours = d.interval_hours ?? 24;
    scheduleConfig.keep_count = d.keep_count ?? 7;
    scheduleConfig.time_of_day = d.time_of_day ?? "02:00";
    scheduleRunning.value = d.running ?? false;
  } catch {
    /* ignore */
  }
}

async function saveSchedule() {
  savingSchedule.value = true;
  try {
    await request.put("/system/backup/schedule", {
      enabled: scheduleConfig.enabled,
      interval_hours: scheduleConfig.interval_hours,
      keep_count: scheduleConfig.keep_count,
      time_of_day: scheduleConfig.time_of_day,
    });
    ElMessage.success("定时备份配置已保存");
    loadSchedule();
  } catch {
    ElMessage.error("保存定时备份配置失败");
  } finally {
    savingSchedule.value = false;
  }
}

onMounted(() => {
  loadBackups();
  loadSchedule();
});
</script>

<style scoped lang="scss">
.backup-section {
  .stats-card {
    margin-bottom: 20px;

    .action-buttons {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      height: 100%;
      align-items: center;
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .restore-info {
    margin-top: 20px;
    padding: 15px;
    background: #f5f7fa;
    border-radius: 4px;

    p {
      margin: 8px 0;
    }
  }
}
</style>
