<template>
  <el-form :model="model"
    ><el-form-item v-for="(f, i) in fields" :key="i" :label="f.label"
      ><el-input
        v-if="f.type === 'text' || !f.type"
        v-model="model[f.key]" /><el-select
        v-else-if="f.type === 'select'"
        v-model="model[f.key]"
        :options="f.options" /></el-form-item
  ></el-form>
</template>
<script setup lang="ts">
defineProps<{
  model: Record<string, any>;
  fields: { key: string; label: string; type?: string; options?: any[] }[];
}>();
</script>
