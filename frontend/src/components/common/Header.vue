<template>
  <div class="app-header">
    <div class="header-left">
      <slot name="left">
        <span class="header-title">{{ title }}</span>
      </slot>
    </div>
    <div class="header-right">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 56px;
  border-bottom: 1px solid rgba(64, 145, 108, 0.3);
}
.header-title {
  font-size: 16px;
  font-weight: bold;
}
</style>
