<template>
  <div class="template-download">
    <el-row :gutter="16">
      <el-col v-for="tpl in displayTemplates" :key="tpl.type" :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" :body-style="{ padding: '20px', textAlign: 'center' }">
          <el-icon :size="36" color="#409EFF"><Document /></el-icon>
          <h4 style="margin: 12px 0 4px; font-size: 15px">{{ tpl.label }}模板</h4>
          <p style="color: #909399; font-size: 12px; margin-bottom: 16px; min-height: 32px">
            {{ tpl.desc }}
          </p>
          <el-button
            type="primary"
            size="small"
            :loading="downloading === tpl.type"
            @click="handleDownload(tpl.type)"
          >
            <el-icon style="margin-right: 4px"><Download /></el-icon>
            下载模板
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document } from '@element-plus/icons-vue'
import { parseContentDisposition, downloadBlob } from '@/api/request'

export interface TemplateOption {
  type: string
  label: string
  desc: string
}

const props = withDefaults(
  defineProps<{
    /** 模板类型列表，为空则显示全部 */
    types?: string[]
    /** 自定义模板列表 */
    templates?: TemplateOption[]
  }>(),
  {
    types: undefined,
    templates: undefined,
  }
)

const ALL_TEMPLATES: TemplateOption[] = [
  {
    type: 'supported_village',
    label: '帮扶村',
    desc: '村名、县市、帮扶单位、地域属性等字段',
  },
  {
    type: 'project',
    label: '项目',
    desc: '项目名称、类型、预算、开始/结束日期等字段',
  },
  { type: 'fund', label: '资金', desc: '经费名称、金额、来源、用途等字段' },
  {
    type: 'school',
    label: '学校',
    desc: '学校名称、类型、学生数、教师数等字段',
  },
]

/** 根据 props 过滤显示的模板 */
const displayTemplates = computed(() => {
  if (props.templates?.length) return props.templates
  const all = ALL_TEMPLATES
  if (props.types?.length) {
    return all.filter((t) => props.types!.includes(t.type))
  }
  return all
})

const downloading = ref('')

/** 触发模板下载（解析后端 Content-Disposition 文件名，避免浏览器误用 "UTF-8"） */
async function handleDownload(type: string) {
  downloading.value = type
  try {
    // 直接走带保存逻辑的封装：内部解析 filename*=UTF-8''xxx 并 decodeURIComponent
    const tpl = ALL_TEMPLATES.find((t) => t.type === type)
    // 用 axios 直接拿响应头；downloadImportTemplate 只返回 Blob 丢失了 headers
    const response = await import('@/api/request').then((m) =>
      m.default.get(`/import/template`, {
        params: { entity_type: type },
        responseType: 'blob',
      })
    )
    const filename = parseContentDisposition(
      response.headers as Record<string, string>,
      `${tpl?.label || type}_导入模板.xlsx`
    )
    downloadBlob(response.data, filename)
    // 下载成功无提示 — 浏览器下载栏已确认
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '模板下载失败，请重试')
  } finally {
    downloading.value = ''
  }
}
</script>

<style scoped>
.template-download {
  width: 100%;
}
</style>
