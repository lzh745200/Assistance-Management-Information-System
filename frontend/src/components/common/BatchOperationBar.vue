<template>
  <div v-if="selectedCount" class="batch-bar">
    <span>已选 {{ selectedCount }} 项</span><slot />
  </div>
</template>
<script setup lang="ts">
defineProps<{ selectedCount?: number }>()
</script>
