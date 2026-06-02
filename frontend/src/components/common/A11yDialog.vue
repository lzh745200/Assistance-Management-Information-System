<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    :aria-label="title"
    role="dialog"
    @update:model-value="$emit('close')"
  >
    <slot />
  </el-dialog>
</template>
<script setup lang="ts">
defineProps<{ visible: boolean; title?: string }>();
defineEmits<{ (e: "close"): void }>();
</script>
