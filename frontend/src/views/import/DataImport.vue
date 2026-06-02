<template>
  <div class="data-import">
    <el-card
      ><el-upload drag action="#" :auto-upload="false"
        ><el-icon><Upload /></el-icon>
        <div>拖拽或点击上传文件</div></el-upload
      ></el-card
    >
  </div>
</template>
<script setup lang="ts">
import { Upload } from "@element-plus/icons-vue";
</script>
