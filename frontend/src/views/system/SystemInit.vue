<template>
  <div class="system-init">
    <el-card
      ><el-steps :active="step" finish-status="success"
        ><el-step title="数据库初始化" /><el-step title="管理员创建" /><el-step
          title="系统配置" /></el-steps
    ></el-card>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
const step = ref(0);
</script>
