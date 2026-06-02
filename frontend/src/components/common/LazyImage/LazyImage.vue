<template><el-image :src="src" :alt="alt" fit="cover" lazy /></template>
<script setup lang="ts">
defineProps<{ src: string; alt?: string }>();
</script>
