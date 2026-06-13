<template>
  <div class="quick-actions">
    <!-- 核心业务 -->
    <div class="action-group">
      <span class="group-label">核心业务</span>
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
      </div>
    </div>

    <!-- 数据与分析 -->
    <div class="action-group">
      <span class="group-label">数据与分析</span>
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
      </div>
    </div>

    <!-- 审批与流程 -->
    <div class="action-group">
      <span class="group-label">审批与流程</span>
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
      </div>
    </div>

    <!-- 系统管理 -->
    <div v-if="isManager || isAdmin" class="action-group">
      <span class="group-label">系统管理</span>
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
      </div>
    </div>

    <div class="action-footer">
      <button class="action-btn layout-btn" @click="$emit('toggleLayout')">
        <span class="btn-icon">⚙️</span>自定义布局
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouterSafe } from "@/composables/useRouterSafe";

defineProps<{
  isManager: boolean;
  isAdmin: boolean;
  backingUp: boolean;
}>();

defineEmits<{
  backup: [];
  restore: [];
  toggleLayout: [];
}>();

const { pushSafe } = useRouterSafe();
</script>

<style scoped lang="scss">
.quick-actions { display: flex; flex-direction: column; gap: 16px; }
.action-group {
  .group-label { display: block; font-size: 13px; font-weight: 600; color: #909399; margin-bottom: 8px; padding-left: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
}
.action-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 8px; }
.action-footer { padding-top: 4px; border-top: 1px solid #ebeef5; }
.action-btn {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px; border: 1px solid #dcdfe6; border-radius: 8px; background: #fff; cursor: pointer; font-size: 14px; color: #303133; transition: all 0.2s ease; white-space: nowrap;
  &:hover { border-color: #409eff; color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,0.12); transform: translateY(-1px); }
  &:active { transform: translateY(0); }
  &:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
  .btn-icon { font-size: 16px; flex-shrink: 0; }
  .btn-text { overflow: hidden; text-overflow: ellipsis; }
  &.primary { background: #ecf5ff; border-color: #b3d8ff; color: #409eff; &:hover { background: #d9ecff; border-color: #409eff; } }
  &.secondary { background: #fafafa; &:hover { background: #f0f2f5; } }
  &.backup { background: #fdf6ec; border-color: #f5dab1; color: #e6a23c; &:hover { background: #faf0e0; border-color: #e6a23c; } }
  &.restore { background: #fef0f0; border-color: #fbc4c4; color: #f56c6c; &:hover { background: #fde2e2; border-color: #f56c6c; } }
  &.layout-btn { background: transparent; border-style: dashed; color: #909399; width: 100%; justify-content: center; &:hover { color: #409eff; border-color: #409eff; } }
}
</style>
