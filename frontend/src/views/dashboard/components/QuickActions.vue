<template>
  <div class="quick-actions">
    <el-collapse v-model="activeGroups" class="qa-collapse">
      <!-- 核心业务 -->
      <el-collapse-item name="core">
        <template #title>
          <span class="group-header">核心业务</span>
          <el-tag size="small" type="primary" effect="plain">12</el-tag>
        </template>
        <div class="action-grid">
          <button class="action-btn primary" @click="pushSafe('/supported-villages')">
            <span class="btn-icon">🏘️</span><span class="btn-text">帮扶村管理</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/projects')">
            <span class="btn-icon">📋</span><span class="btn-text">项目管理</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/funds')">
            <span class="btn-icon">💰</span><span class="btn-text">经费管理</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/schools')">
            <span class="btn-icon">🏫</span><span class="btn-text">学校管理</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/policies')">
            <span class="btn-icon">📜</span><span class="btn-text">政策文件</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/organization')">
            <span class="btn-icon">🏛️</span><span class="btn-text">组织架构</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/projects/import')">
            <span class="btn-icon">📥</span><span class="btn-text">项目导入</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/funds/apply')">
            <span class="btn-icon">📝</span><span class="btn-text">经费申请</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/rural-works')">
            <span class="btn-icon">🌾</span><span class="btn-text">乡村振兴</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/effectiveness')">
            <span class="btn-icon">🎯</span><span class="btn-text">帮扶成效</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/projects/create')">
            <span class="btn-icon">➕</span><span class="btn-text">新建项目</span>
          </button>
          <button class="action-btn primary" @click="pushSafe('/schools/create')">
            <span class="btn-icon">🏗️</span><span class="btn-text">新建学校</span>
          </button>
        </div>
      </el-collapse-item>

      <!-- 数据与分析 -->
      <el-collapse-item name="data">
        <template #title>
          <span class="group-header">数据与分析</span>
          <el-tag size="small" type="success" effect="plain">11</el-tag>
        </template>
        <div class="action-grid">
          <button class="action-btn secondary" @click="pushSafe('/data-analysis')">
            <span class="btn-icon">📊</span><span class="btn-text">数据分析</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/analysis')">
            <span class="btn-icon">📈</span><span class="btn-text">经费分析</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/schools/analysis')">
            <span class="btn-icon">📉</span><span class="btn-text">学校分析</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/import/data')">
            <span class="btn-icon">📥</span><span class="btn-text">数据导入</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/export/report')">
            <span class="btn-icon">📤</span><span class="btn-text">报表导出</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/data-sync')">
            <span class="btn-icon">🔄</span><span class="btn-text">数据同步</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/data-entry')">
            <span class="btn-icon">✏️</span><span class="btn-text">综合录入</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/work-calendar')">
            <span class="btn-icon">📅</span><span class="btn-text">工作日历</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/data-analysis/map')">
            <span class="btn-icon">🗺️</span><span class="btn-text">地图分析</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/data-analysis/assessment')">
            <span class="btn-icon">📋</span><span class="btn-text">评估分析</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/supported-villages/yearly')">
            <span class="btn-icon">📆</span><span class="btn-text">年度概览</span>
          </button>
        </div>
      </el-collapse-item>

      <!-- 审批与流程 -->
      <el-collapse-item name="workflow">
        <template #title>
          <span class="group-header">审批与流程</span>
          <el-tag size="small" type="warning" effect="plain">11</el-tag>
        </template>
        <div class="action-grid">
          <button class="action-btn secondary" @click="pushSafe('/approval')">
            <span class="btn-icon">✅</span><span class="btn-text">审批中心</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/rural-works/list')">
            <span class="btn-icon">📝</span><span class="btn-text">工作日志</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/message')">
            <span class="btn-icon">💬</span><span class="btn-text">消息中心</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/lifecycle')">
            <span class="btn-icon">🔄</span><span class="btn-text">资金周期</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/contract')">
            <span class="btn-icon">📋</span><span class="btn-text">合同管理</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/anomaly')">
            <span class="btn-icon">⚠️</span><span class="btn-text">异常资金</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/budget')">
            <span class="btn-icon">💵</span><span class="btn-text">经费预算</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/report/templates')">
            <span class="btn-icon">📄</span><span class="btn-text">报表模板</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/todos')">
            <span class="btn-icon">✅</span><span class="btn-text">待办事项</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/report')">
            <span class="btn-icon">📊</span><span class="btn-text">经费报表</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/funds/settlement')">
            <span class="btn-icon">💳</span><span class="btn-text">经费结算</span>
          </button>
        </div>
      </el-collapse-item>

      <!-- 系统管理 -->
      <el-collapse-item v-if="isManager || isAdmin" name="system">
        <template #title>
          <span class="group-header">系统管理</span>
          <el-tag size="small" type="danger" effect="plain">10</el-tag>
        </template>
        <div class="action-grid">
          <button v-if="isManager" class="action-btn backup" :disabled="backingUp" @click="$emit('backup')">
            <span class="btn-icon">💾</span><span class="btn-text">{{ backingUp ? "备份中..." : "一键备份" }}</span>
          </button>
          <button v-if="isAdmin" class="action-btn restore" @click="$emit('restore')">
            <span class="btn-icon">🔧</span><span class="btn-text">恢复数据</span>
          </button>
          <button v-if="isManager || isAdmin" class="action-btn secondary" @click="pushSafe('/system/monitoring')">
            <span class="btn-icon">🖥️</span><span class="btn-text">系统监控</span>
          </button>
          <button v-if="isAdmin" class="action-btn secondary" @click="pushSafe('/system/users')">
            <span class="btn-icon">👥</span><span class="btn-text">用户与角色</span>
          </button>
          <button v-if="isAdmin" class="action-btn secondary" @click="pushSafe('/system/config')">
            <span class="btn-icon">⚙️</span><span class="btn-text">系统配置</span>
          </button>
          <button v-if="isManager" class="action-btn secondary" @click="pushSafe('/system/audit')">
            <span class="btn-icon">📋</span><span class="btn-text">审计日志</span>
          </button>
          <button v-if="isAdmin" class="action-btn secondary" @click="pushSafe('/system/backup')">
            <span class="btn-icon">📦</span><span class="btn-text">备份管理</span>
          </button>
          <button v-if="isAdmin" class="action-btn secondary" @click="pushSafe('/admin/machine-code')">
            <span class="btn-icon">🔑</span><span class="btn-text">机器码管理</span>
          </button>
          <button v-if="isManager" class="action-btn secondary" @click="pushSafe('/data-management/logs')">
            <span class="btn-icon">📜</span><span class="btn-text">操作日志</span>
          </button>
          <button class="action-btn secondary" @click="pushSafe('/help')">
            <span class="btn-icon">📖</span><span class="btn-text">帮助文档</span>
          </button>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouterSafe } from "@/composables/useRouterSafe";

defineProps<{
  isManager: boolean;
  isAdmin: boolean;
  backingUp: boolean;
}>();

defineEmits<{
  backup: [];
  restore: [];
}>();

const { pushSafe } = useRouterSafe();
const activeGroups = ref(["core"]);
</script>

<style scoped lang="scss">
.qa-collapse {
  border: none;
  :deep(.el-collapse-item__header) {
    padding: 10px 14px;
    font-weight: 600;
    font-size: 14px;
    border-radius: 8px;
    &.is-active { color: #1b4332; }
  }
  :deep(.el-collapse-item__wrap) { border: none; }
  :deep(.el-collapse-item__content) { padding: 8px 4px 12px; }
}

.group-header { flex: 1; }

.action-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 6px; }

.action-btn {
  display: flex; align-items: center; gap: 6px; padding: 8px 10px;
  border: 1px solid #dcdfe6; border-radius: 8px; background: #fff;
  cursor: pointer; font-size: 13px; color: #303133;
  transition: all 0.15s ease; white-space: nowrap;
  &:hover { border-color: #409eff; color: #409eff; background: #f0f5ff; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-icon { font-size: 14px; flex-shrink: 0; }
  .btn-text { overflow: hidden; text-overflow: ellipsis; }
  &.primary { background: #ecf5ff; border-color: #b3d8ff; color: #409eff; &:hover { background: #d9ecff; } }
  &.secondary { background: #fafafa; &:hover { background: #f0f2f5; } }
  &.backup { background: #fdf6ec; border-color: #f5dab1; color: #e6a23c; &:hover { background: #faf0e0; } }
  &.restore { background: #fef0f0; border-color: #fbc4c4; color: #f56c6c; &:hover { background: #fde2e2; } }
}
</style>
