<template>
  <div class="image-comparison"><slot /></div>
</template>
<script setup lang="ts">
defineProps<{ before?: string; after?: string; label?: string }>();
</script>
