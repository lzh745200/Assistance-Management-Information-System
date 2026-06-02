<template>
  <el-menu :default-active="active" router
    ><el-menu-item v-for="(item, i) in menuItems" :key="i" :index="item.path">{{
      item.title
    }}</el-menu-item></el-menu
  >
</template>
<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
const route = useRoute();
const active = computed(() => route.path);
defineProps<{ menuItems: { path: string; title: string }[] }>();
</script>
