<template>
  <div class="quick-actions">
    <button class="action-btn primary" @click="pushSafe('/projects')">
      <span class="btn-icon">+</span> 新建项目
    </button>
    <button class="action-btn secondary" @click="pushSafe('/data-analysis')">
      <span class="btn-icon">📊</span> 数据分析
    </button>
    <button
      v-if="isManager"
      class="action-btn backup"
      :disabled="backingUp"
      @click="$emit('backup')"
    >
      <span class="btn-icon">💾</span>
      {{ backingUp ? "备份中..." : "一键备份" }}
    </button>
    <button
      v-if="isAdmin"
      class="action-btn restore"
      @click="$emit('restore')"
    >
      <span class="btn-icon">🔄</span> 恢复数据
    </button>
    <button
      v-if="!isManager"
      class="action-btn secondary"
      @click="pushSafe('/data-package')"
    >
      <span class="btn-icon">📤</span> 数据上报
    </button>
    <button class="action-btn layout-btn" @click="$emit('toggleLayout')">
      <span class="btn-icon">⚙️</span> 自定义布局
    </button>
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
