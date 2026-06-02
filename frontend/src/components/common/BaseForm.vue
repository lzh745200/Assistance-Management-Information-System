<template>
  <el-form :model="model" :rules="rules" :label-width="labelWidth"
    ><slot
  /></el-form>
</template>
<script setup lang="ts">
defineProps<{
  model: Record<string, any>;
  rules?: Record<string, any>;
  labelWidth?: string;
}>();
</script>
