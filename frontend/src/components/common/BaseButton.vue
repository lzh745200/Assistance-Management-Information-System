<template>
  <el-button v-bind="$attrs" :type="type" :size="size" :loading="loading" :disabled="disabled">
    <slot />
  </el-button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | ''
    size?: 'large' | 'default' | 'small'
    loading?: boolean
    disabled?: boolean
  }>(),
  { type: '', size: 'default', loading: false, disabled: false }
)
</script>
