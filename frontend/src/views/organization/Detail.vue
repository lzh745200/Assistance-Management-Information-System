<template>
  <div class="organization-detail">
    <el-card v-loading="loading" class="detail-card">
      <template #header>
        <div class="card-header">
          <span class="title">组织详情</span>
          <div class="actions">
            <el-button type="primary" @click="handleEdit">编辑</el-button>
            <el-button @click="handleBack">返回</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="组织名称">{{ org.name }}</el-descriptions-item>
        <el-descriptions-item label="组织编码">{{ org.code }}</el-descriptions-item>
        <el-descriptions-item label="层级">{{ org.level }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="org.is_active ? 'success' : 'info'">
            {{ org.is_active ? '正常' : '停用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="联系人">{{
          ds(org.contact_person, 'name') || '无'
        }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{
          ds(org.contact_phone, 'phone') || '无'
        }}</el-descriptions-item>
        <el-descriptions-item label="地址" :span="2">{{
          ds(org.address, 'address') || '无'
        }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{
          org.description || '无'
        }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{
          formatDate(org.created_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{
          formatDate(org.updated_at)
        }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { logger } from '@/utils/logger'

import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useRouterSafe, safeRouteParam } from '@/composables/useRouterSafe'
import { useDesensitize } from '@/composables/useDesensitize'
import { ElMessage } from 'element-plus'
import { getOrganization } from '@/api/organization'

const { pushSafe } = useRouterSafe()
const { ds } = useDesensitize()
const route = useRoute()
const loading = ref(false)

const org = ref({
  id: 0,
  name: '',
  code: '',
  level: 0,
  is_active: true,
  contact_person: '',
  contact_phone: '',
  address: '',
  description: '',
  created_at: '',
  updated_at: '',
})

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '无'
  return dateStr.split('T')[0]
}

const loadData = async () => {
  const id = safeRouteParam(route.params.id)
  if (!id) return

  loading.value = true
  try {
    const data = await getOrganization(id)
    org.value = {
      id: data.id,
      name: data.name || '',
      code: data.code || '',
      level: data.level || 0,
      is_active: data.is_active !== false,
      contact_person: data.contact_person || '',
      contact_phone: data.contact_phone || '',
      address: data.address || '',
      description: data.description || '',
      created_at: data.created_at || '',
      updated_at: data.updated_at || '',
    }
  } catch (error) {
    logger.error('加载组织信息失败:', error)
    ElMessage.error('加载组织信息失败')
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  pushSafe(`/organizations/${org.value.id}/edit`)
}

const handleBack = () => {
  pushSafe('/organizations')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.organization-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
}

.actions {
  display: flex;
  gap: 10px;
}
</style>
