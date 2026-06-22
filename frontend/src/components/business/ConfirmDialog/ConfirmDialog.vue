<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    width="420px"
    @update:model-value="$emit('cancel')"
  >
    <p>{{ message }}</p>
    <template #footer>
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="$emit('confirm')">确认</el-button>
    </template>
  </el-dialog>
</template>
<script setup lang="ts">
defineProps<{ visible: boolean; title?: string; message?: string }>()
defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>()
</script>
