<template>
  <el-dialog
    :model-value="visible"
    :title="title"
    :width="width"
    @update:model-value="$emit('close')"
    ><slot /><template #footer v-if="$slots.footer"
      ><slot name="footer" /></template
  ></el-dialog>
</template>
<script setup lang="ts">
defineProps<{ visible: boolean; title?: string; width?: string }>();
defineEmits<{ (e: "close"): void }>();
</script>
