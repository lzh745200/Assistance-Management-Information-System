<template>
  <el-input
    :model-value="modelValue"
    :placeholder="placeholder"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>
<script setup lang="ts">
defineProps<{ modelValue?: string; placeholder?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()
</script>
