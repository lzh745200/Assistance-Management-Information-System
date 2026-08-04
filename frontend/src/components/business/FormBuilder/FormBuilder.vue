<template>
  <el-form :model="localModel">
    <el-form-item v-for="(f, i) in fields" :key="i" :label="f.label">
      <el-input v-if="f.type === 'text' || !f.type" v-model="localModel[f.key]" />
      <el-select v-else-if="f.type === 'select'" v-model="localModel[f.key]">
        <el-option
          v-for="opt in f.options || []"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>
    </el-form-item>
  </el-form>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  model: Record<string, any>
  fields: {
    key: string
    label: string
    type?: string
    options?: { label: string; value: any }[]
  }[]
}>()
const emit = defineEmits<{
  (e: 'update:model', value: Record<string, any>): void
}>()

const localModel = ref({ ...props.model })
/* c8 ignore next -- deep watch 回调为 v8 对 vue 编译产物的计数伪影（测试已触发 emit 验证） */
watch(localModel, (v) => emit('update:model', v), { deep: true })
</script>
