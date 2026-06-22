<template>
  <div class="school-support">
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ schoolInfo.name }} - 帮扶记录</span>
          <el-button @click="handleBack">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="4" border>
        <el-descriptions-item label="学校类型">{{ schoolInfo.type }}</el-descriptions-item>
        <el-descriptions-item label="所在地区">{{ schoolInfo.location }}</el-descriptions-item>
        <el-descriptions-item label="帮扶单位">{{ schoolInfo.supportUnit }}</el-descriptions-item>
        <el-descriptions-item label="帮扶状态">
          <el-tag :type="schoolInfo.status === 'active' ? 'success' : 'info'">
            {{ schoolInfo.status === 'active' ? '帮扶中' : '已完成' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="records-card">
      <template #header>
        <div class="card-header">
          <span class="title">帮扶记录列表</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增记录
          </el-button>
        </div>
      </template>

      <el-timeline>
        <el-timeline-item
          v-for="item in records"
          :key="item.id"
          :timestamp="item.date"
          placement="top"
          :type="item.type"
        >
          <el-card>
            <h4>{{ item.title }}</h4>
            <p class="record-content">{{ item.content }}</p>
            <div class="record-meta">
              <el-tag size="small">{{ item.category }}</el-tag>
              <span v-if="item.amount" class="amount">投入: {{ item.amount }}万元</span>
              <span v-if="item.participants" class="participants"
                >参与人数: {{ item.participants }}人</span
              >
            </div>
            <div class="record-actions">
              <el-button size="small" type="primary" @click="handleEdit(item)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(item)">删除</el-button>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="记录标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入记录标题" />
        </el-form-item>
        <el-form-item label="记录类别" prop="category">
          <el-select v-model="formData.category" placeholder="请选择" style="width: 100%">
            <el-option label="基础设施" value="infrastructure" />
            <el-option label="教学设备" value="equipment" />
            <el-option label="师资培训" value="training" />
            <el-option label="助学金" value="scholarship" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="formData.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="投入金额" prop="amount">
          <el-input-number
            v-model="formData.amount"
            :min="0"
            :precision="2"
            controls-position="right"
            style="width: 100%"
          >
            <template #append>万元</template>
          </el-input-number>
        </el-form-item>
        <el-form-item label="参与人数" prop="participants">
          <el-input-number
            v-model="formData.participants"
            :min="0"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="记录内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="4"
            placeholder="请输入记录内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { localDatabase } from '@/utils/LocalDatabase'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()

const schoolInfo = reactive({
  id: '',
  name: '',
  type: '',
  location: '',
  supportUnit: '',
  status: '',
})

const records = ref<any[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('新增帮扶记录')
const isEdit = ref(false)

const formData = reactive({
  id: '',
  schoolId: '',
  title: '',
  category: '',
  date: '',
  amount: 0,
  participants: 0,
  content: '',
  type: 'success',
})

const rules = {
  title: [{ required: true, message: '请输入记录标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择记录类别', trigger: 'change' }],
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  content: [{ required: true, message: '请输入记录内容', trigger: 'blur' }],
}

const loadSchoolInfo = async (id: string) => {
  try {
    const result = await localDatabase.get('school', id)
    if (result) {
      Object.assign(schoolInfo, result)
    }
  } catch (error) {
    logger.error('加载学校信息失败:', error)
  }
}

const loadRecords = async (schoolId: string) => {
  try {
    const allRecords = await localDatabase.query('school_support', {
      schoolId,
    })
    records.value = allRecords || []
  } catch (error) {
    logger.error('加载帮扶记录失败:', error)
  }
}

const handleAdd = () => {
  isEdit.value = false
  dialogTitle.value = '新增帮扶记录'
  Object.assign(formData, {
    id: '',
    schoolId: schoolInfo.id,
    title: '',
    category: '',
    date: '',
    amount: 0,
    participants: 0,
    content: '',
    type: 'success',
  })
  dialogVisible.value = true
}

const handleEdit = (item: any) => {
  isEdit.value = true
  dialogTitle.value = '编辑帮扶记录'
  Object.assign(formData, item)
  dialogVisible.value = true
}

const handleDelete = async (item: any) => {
  try {
    await ElMessageBox.confirm('确定删除该记录吗？', '提示', {
      type: 'warning',
    })
    await localDatabase.delete('school_support', item.id)
    ElMessage.success('删除成功')
    loadRecords(schoolInfo.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (isEdit.value) {
          await localDatabase.update('school_support', formData)
          ElMessage.success('修改成功')
        } else {
          formData.id = `support_${Date.now()}`
          await localDatabase.set('school_support', formData)
          ElMessage.success('添加成功')
        }
        dialogVisible.value = false
        loadRecords(schoolInfo.id)
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
  })
}

const handleCancel = () => {
  dialogVisible.value = false
}

const handleBack = () => {
  router.back()
}

onMounted(() => {
  const id = route.params.id as string
  if (id) {
    loadSchoolInfo(id)
    loadRecords(id)
  }
})
</script>

<style scoped>
.school-support {
  padding: 20px;
}

.info-card,
.records-card {
  margin-bottom: 20px;
  background: rgba(10, 30, 20, 0.5);
  border: 1px solid rgba(64, 145, 108, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
}

.record-content {
  margin: 10px 0;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
}

.record-meta {
  display: flex;
  gap: 15px;
  align-items: center;
  margin: 10px 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.record-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
  border-bottom: 1px solid rgba(64, 145, 108, 0.3);
  color: #fff;
}

:deep(.el-timeline-item__wrapper) {
  padding-left: 28px;
}

:deep(.el-timeline-item__card) {
  background: rgba(10, 30, 20, 0.3);
  border: 1px solid rgba(64, 145, 108, 0.2);
}
</style>
