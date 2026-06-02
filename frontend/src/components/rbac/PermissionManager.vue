<template>
  <el-checkbox-group
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    ><el-checkbox v-for="p in permissions" :key="p.key" :label="p.key">{{
      p.label
    }}</el-checkbox></el-checkbox-group
  >
</template>
<script setup lang="ts">
defineProps<{
  modelValue?: string[];
  permissions: { key: string; label: string }[];
}>();
defineEmits<{ (e: "update:modelValue", v: string[]): void }>();
</script>
