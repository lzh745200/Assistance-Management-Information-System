<template>
  <el-dialog
    :model-value="visible"
    title="变更历史"
    width="600px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <el-timeline>
      <el-timeline-item v-for="(item, i) in history" :key="i" :timestamp="item.time">
        {{ item.action }} by {{ item.user }}
      </el-timeline-item>
    </el-timeline>
  </el-dialog>
</template>
<script setup lang="ts">
defineProps<{
  visible: boolean
  history?: { time: string; action: string; user: string }[]
}>()
defineEmits<{ (e: 'update:visible', v: boolean): void }>()
</script>
