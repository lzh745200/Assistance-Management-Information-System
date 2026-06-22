<template>
  <el-container class="enhanced-layout">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'">
      <slot name="sidebar" />
    </el-aside>
    <el-container>
      <el-header><slot name="header" /></el-header>
      <el-main><slot /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const sidebarCollapsed = ref(false)
</script>

<style scoped>
.enhanced-layout {
  height: 100vh;
}
</style>
