<template><div ref="mapRef" :style="{ height: height + 'px' }"></div></template>
<script setup lang="ts">
defineProps<{ height?: number; data?: any[] }>();
</script>
