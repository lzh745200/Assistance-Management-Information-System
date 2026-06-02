<template>
  <div class="before-after-slider"><slot /></div>
</template>
<script setup lang="ts">
defineProps<{ before?: string; after?: string }>();
</script>
