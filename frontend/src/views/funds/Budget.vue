<template>
  <div class="budget-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="pushSafe('/funds')">返回经费管理</el-button>
        <h2 class="page-title">预算管理</h2>
      </div>
      <div class="header-actions">
        <el-select
          v-model="selectedYear"
          placeholder="选择年份"
          style="width: 120px; margin-right: 10px"
        >
          <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
        </el-select>
        <el-button type="primary" @click="handleAddBudget">
          <el-icon><Plus /></el-icon>新增预算
        </el-button>
      </div>
    </div>

    <!-- 预算汇总 -->
    <div class="stats-row">
      <div class="stat-item">
        <div class="stat-value">{{ summary.totalBudget }}</div>
        <div class="stat-label">年度总预算(万元)</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-success">{{ summary.totalUsed }}</div>
        <div class="stat-label">已使用(万元)</div>
      </div>
      <div class="stat-item">
        <div class="stat-value text-info">{{ summary.totalRemaining }}</div>
        <div class="stat-label">剩余(万元)</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" :class="usageRateClass">{{ summary.usageRate }}%</div>
        <div class="stat-label">使用率</div>
      </div>
    </div>

    <!-- 预算分配表 -->
    <div class="detail-card">
      <div class="card-header">
        <h3>{{ selectedYear }}年度预算分配</h3>
      </div>
      <div class="card-body">
        <el-table :data="budgetData" stripe show-summary :summary-method="getSummary">
          <el-table-column prop="category" label="预算类别" width="160" />
          <el-table-column prop="budget" label="预算金额(万元)" width="140" align="right">
            <template #default="{ row }">
              <span class="amount-text">{{ row.budget.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="used" label="已使用(万元)" width="140" align="right">
            <template #default="{ row }">
              {{ row.used.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="剩余(万元)" width="140" align="right">
            <template #default="{ row }">
              <span :class="{ 'text-danger': row.budget - row.used < 0 }">
                {{ (row.budget - row.used).toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="使用率" width="200">
            <template #default="{ row }">
              <el-progress
                :percentage="
                  row.budget > 0 ? Math.min(Math.round((row.used / row.budget) * 100), 100) : 0
                "
                :color="getProgressColor(row.budget > 0 ? (row.used / row.budget) * 100 : 0)"
                :stroke-width="10"
              />
            </template>
          </el-table-column>
          <el-table-column
            prop="remark"
            label="备注/结余原因"
            min-width="150"
            show-overflow-tooltip
          />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDeleteBudget(row)">
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-if="budgetData.length === 0 && !loading"
          description="暂无预算记录，点击“新增预算”添加"
        />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingItem ? '编辑预算' : '新增预算'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="年度" prop="year">
              <el-input-number v-model="form.year" :min="2000" :max="2050" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预算类别" prop="category">
              <el-input
                v-model="form.category"
                placeholder="如：项目经费、教育帮扶"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="预算(万元)" prop="budget_amount">
              <el-input-number
                v-model="form.budget_amount"
                :min="0"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="已使用(万元)" prop="used_amount">
              <el-input-number
                v-model="form.used_amount"
                :min="0"
                :precision="2"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="结余原因">
          <el-input v-model="form.remaining_reason" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveBudget">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, watch, onMounted } from 'vue'
import { useRouterSafe } from '@/composables/useRouterSafe'
import { ElMessage, type FormInstance } from 'element-plus'
import { logger } from '@/utils/logger'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { fundApi } from '@/api/funds'

interface BudgetRow {
  id?: number
  year: number
  category: string
  budget_amount: number
  used_amount: number
  remaining_reason?: string
  remarks?: string
  budget: number
  used: number
  remark: string
}

const { pushSafe } = useRouterSafe()

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: currentYear - 2000 + 2 }, (_, i) => 2000 + i)
const selectedYear = ref(currentYear)
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editingItem = ref<BudgetRow | null>(null)
const formRef = ref<FormInstance | null>(null)

const budgetData = ref<BudgetRow[]>([])

const formRules = {
  category: [
    { required: true, message: '请输入预算类别', trigger: 'blur' },
    { max: 50, message: '最多 50 个字符', trigger: 'blur' },
  ],
  budget_amount: [
    { required: true, message: '请输入预算金额', trigger: 'change' },
    {
      type: 'number' as const,
      min: 0,
      message: '预算金额不能为负数',
      trigger: 'change',
    },
  ],
  used_amount: [
    { required: true, message: '请输入已使用金额', trigger: 'change' },
    {
      type: 'number' as const,
      min: 0,
      message: '已使用金额不能为负数',
      trigger: 'change',
    },
  ],
}

const form = ref({
  year: currentYear,
  category: '',
  budget_amount: 0,
  used_amount: 0,
  remaining_reason: '',
  remarks: '',
})

async function loadBudgets() {
  loading.value = true
  try {
    const res = await fundApi.listBudgets(selectedYear.value)
    budgetData.value = (res.items || []).map((r: unknown) => {
      const item = r as Record<string, unknown>
      return {
        id: item.id as number | undefined,
        year: Number(item.year) || 0,
        category: String(item.category || ''),
        budget_amount: Number(item.budget_amount) || 0,
        used_amount: Number(item.used_amount) || 0,
        remaining_reason: item.remaining_reason ? String(item.remaining_reason) : undefined,
        remarks: item.remarks ? String(item.remarks) : undefined,
        budget: Number(item.budget_amount) || 0,
        used: Number(item.used_amount) || 0,
        remark: String(item.remarks || item.remaining_reason || ''),
      } as BudgetRow
    })
  } catch (error) {
    logger.error('加载预算数据失败', error)
    ElMessage.error('加载预算数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function openDialog(row?: BudgetRow) {
  editingItem.value = row || null
  if (row) {
    form.value = {
      year: row.year,
      category: row.category,
      budget_amount: row.budget_amount,
      used_amount: row.used_amount,
      remaining_reason: row.remaining_reason || '',
      remarks: row.remarks || '',
    }
  } else {
    form.value = {
      year: selectedYear.value,
      category: '',
      budget_amount: 0,
      used_amount: 0,
      remaining_reason: '',
      remarks: '',
    }
  }
  dialogVisible.value = true
}

async function handleSaveBudget() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingItem.value) {
      if (!editingItem.value.id) {
        ElMessage.error('无法保存：记录 ID 无效')
        return
      }
      await fundApi.updateBudget(editingItem.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await fundApi.createBudget(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadBudgets()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteBudget(row: BudgetRow) {
  if (!row.id) {
    ElMessage.error('无法删除：记录 ID 无效')
    return
  }
  try {
    await fundApi.deleteBudget(row.id)
    ElMessage.success('删除成功')
    loadBudgets()
  } catch (error) {
    logger.error('删除预算失败', error)
    ElMessage.error('删除预算失败，请稍后重试')
  }
}

const summary = computed(() => {
  const totalBudget = budgetData.value.reduce((sum, r) => sum + (r.budget || 0), 0)
  const totalUsed = budgetData.value.reduce((sum, r) => sum + (r.used || 0), 0)
  const totalRemaining = totalBudget - totalUsed
  const usageRate = totalBudget > 0 ? Math.round((totalUsed / totalBudget) * 100) : 0
  return {
    totalBudget: totalBudget.toFixed(2),
    totalUsed: totalUsed.toFixed(2),
    totalRemaining: totalRemaining.toFixed(2),
    usageRate,
  }
})

const usageRateClass = computed(() => {
  const rate = summary.value.usageRate
  if (rate >= 90) return 'text-danger'
  if (rate >= 60) return 'text-warning'
  return 'text-success'
})

function getProgressColor(rate: number) {
  if (rate >= 90) return '#f56c6c'
  if (rate >= 70) return '#e6a23c'
  return '#40916c'
}

function getSummary({ columns, data }: { columns: unknown[]; data: BudgetRow[] }) {
  const sums: string[] = []
  columns.forEach((_col, index: number) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    if (index === 1) {
      sums[index] = data.reduce((s: number, r) => s + (r.budget || 0), 0).toFixed(2)
      return
    }
    if (index === 2) {
      sums[index] = data.reduce((s: number, r) => s + (r.used || 0), 0).toFixed(2)
      return
    }
    if (index === 3) {
      sums[index] = (
        data.reduce((s: number, r) => s + (r.budget || 0), 0) -
        data.reduce((s: number, r) => s + (r.used || 0), 0)
      ).toFixed(2)
      return
    }
    sums[index] = ''
  })
  return sums
}

function handleAddBudget() {
  openDialog()
}

watch(selectedYear, () => loadBudgets())
onMounted(() => loadBudgets())
</script>

<style scoped>
.budget-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1b4332;
}

.header-actions {
  display: flex;
  align-items: center;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  flex: 1;
  background: linear-gradient(135deg, rgba(27, 67, 50, 0.08) 0%, rgba(45, 106, 79, 0.05) 100%);
  border: 1px solid rgba(45, 106, 79, 0.2);
  border-radius: 8px;
  padding: 16px 20px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1b4332;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

.text-success {
  color: #40916c;
}
.text-info {
  color: #409eff;
}
.text-warning {
  color: #e6a23c;
}
.text-danger {
  color: #f56c6c;
}
.text-success-text {
  color: #40916c;
}

/* 卡片 */
.detail-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  overflow: hidden;
}

.card-header {
  padding: 16px 24px;
  background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%);
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.card-body {
  padding: 24px;
}

.amount-text {
  font-weight: 600;
  color: #1b4332;
}
</style>
