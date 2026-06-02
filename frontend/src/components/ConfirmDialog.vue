<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="confirm-content">
      <el-icon v-if="type === 'warning'" class="confirm-icon warning"><WarningFilled /></el-icon>
      <el-icon v-else-if="type === 'danger'" class="confirm-icon danger"><CircleCloseFilled /></el-icon>
      <el-icon v-else class="confirm-icon info"><InfoFilled /></el-icon>
      <p class="confirm-message">{{ message }}</p>
    </div>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button :type="confirmType" :loading="loading" @click="handleConfirm">{{ confirmText }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  message: string
  type?: 'info' | 'warning' | 'danger'
  confirmText?: string
  loading?: boolean
  width?: string
}>(), {
  title: '确认操作',
  type: 'warning',
  confirmText: '确认',
  loading: false,
  width: '420px',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val: boolean) => emit('update:modelValue', val),
})

const confirmType = computed(() => props.type === 'danger' ? 'danger' : 'primary')

function handleClose() { visible.value = false }
function handleConfirm() { emit('confirm') }
</script>

<style scoped>
.confirm-content { display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; }
.confirm-icon { font-size: 24px; flex-shrink: 0; margin-top: 2px; }
.confirm-icon.warning { color: #e6a23c; }
.confirm-icon.danger { color: #f56c6c; }
.confirm-icon.info { color: #409eff; }
.confirm-message { font-size: 14px; color: #333; line-height: 1.6; margin: 0; }
</style>
