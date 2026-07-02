<template>
  <div v-loading="loading" class="yearly-overview-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <el-button text @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>返回详情
        </el-button>
        <h2 class="page-title">{{ villageName }} — 年度数据管理</h2>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedYear" style="width: 120px" @change="loadAllData">
          <el-option
            v-for="year in availableYears"
            :key="year"
            :label="`${year}年`"
            :value="year"
          />
        </el-select>
        <el-button type="primary" :loading="downloadingAll" @click="handleDownloadAllTemplates">
          <el-icon><Download /></el-icon>全部模板下载
        </el-button>
        <el-upload
          :show-file-list="false"
          :before-upload="() => false"
          :on-change="handleImportAll"
          accept=".xlsx,.xls"
          class="inline-upload"
        >
          <el-button type="success" :loading="importingAll">
            <el-icon><Upload /></el-icon>全部导入
          </el-button>
        </el-upload>
      </div>
    </div>

    <!-- 板块卡片网格 -->
    <div class="section-grid">
      <div v-for="section in sections" :key="section.key" class="section-card">
        <div class="section-card-header">
          <span class="section-icon">{{ section.icon }}</span>
          <h3>{{ section.title }}</h3>
        </div>
        <div class="section-summary">
          <div v-for="stat in section.stats" :key="stat.label" class="summary-item">
            <span class="summary-value">{{ stat.value }}</span>
            <span class="summary-label">{{ stat.label }}</span>
          </div>
          <div v-if="!section.stats.length" class="no-data-hint">暂无数据</div>
        </div>
        <div class="section-card-actions">
          <el-button size="small" type="primary" @click="openEditDialog(section.key)">
            <el-icon><Edit /></el-icon>填写
          </el-button>
          <el-button size="small" @click="handleDownloadTemplate(section.key)">
            <el-icon><Download /></el-icon>模板
          </el-button>
          <el-upload
            :show-file-list="false"
            :before-upload="() => false"
            :on-change="(file: any) => handleImportSection(section.key, file)"
            accept=".xlsx,.xls"
            class="inline-upload"
          >
            <el-button size="small">
              <el-icon><Upload /></el-icon>导入
            </el-button>
          </el-upload>
        </div>
      </div>
    </div>

    <!-- 年度数据编辑弹窗（按板块独立填写） -->
    <el-dialog
      v-model="editDialogVisible"
      :title="`${editSectionTitle} — 数据填写`"
      width="900px"
      destroy-on-close
    >
      <SectionDataForm
        v-if="editDialogVisible"
        :village-id="villageId"
        :village-name="villageName"
        :section-key="editSectionKey"
        :initial-year="selectedYear"
        @close="editDialogVisible = false"
        @saved="loadAllData"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useRouterSafe, safeRouteParam } from '@/composables/useRouterSafe'
import { ArrowLeft, Edit, Download, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getSupportedVillage,
  getYearlyData,
  downloadTemplate,
  importSectionData,
  downloadAllTemplates,
  importAllSectionsData,
} from '@/api/supportedVillage'
import type { YearlyDataSummary } from '@/types/analytics'
import SectionDataForm from './components/SectionDataForm.vue'
import { unwrapData } from '@/utils/unwrapData'

const route = useRoute()
const { pushSafe } = useRouterSafe()

const villageId = computed(() => safeRouteParam(route.params.id))
const villageName = ref('')
const loading = ref(false)
const downloadingAll = ref(false)
const importingAll = ref(false)
const selectedYear = ref(new Date().getFullYear())
const yearlyData = ref<YearlyDataSummary | null>(null)

const availableYears = computed(() => {
  const years: number[] = []
  for (let y = 2017; y <= new Date().getFullYear() + 1; y++) {
    years.push(y)
  }
  return years.reverse()
})

// 弹窗
const editDialogVisible = ref(false)
const editSectionKey = ref('')
const editSectionTitle = ref('')

// 板块定义
const sections = computed(() => {
  const d = yearlyData.value
  return [
    {
      key: 'population',
      title: '人口数据',
      icon: '👥',
      stats: d?.population
        ? [
            { label: '总人口', value: d.population.totalPopulation ?? 0 },
            { label: '总户数', value: d.population.totalHouseholds ?? 0 },
            { label: '常住人口', value: d.population.residentPopulation ?? 0 },
          ]
        : [],
    },
    {
      key: 'income',
      title: '收入数据',
      icon: '💰',
      stats: d?.income
        ? [
            {
              label: '人均收入(万)',
              value: (d.income.perCapitaIncome ?? 0).toFixed(2),
            },
            {
              label: '集体收入(万)',
              value: (d.income.collectiveIncome ?? 0).toFixed(2),
            },
          ]
        : [],
    },
    {
      key: 'force_investment',
      title: '力量投入',
      icon: '🎖️',
      stats: d?.['force-investment']
        ? [
            {
              label: '领导到村(人次)',
              value: d['force-investment'].seniorLeaderVisits ?? 0,
            },
            {
              label: '官兵到村(人次)',
              value: d['force-investment'].unitSoldierVisits ?? 0,
            },
          ]
        : [],
    },
    {
      key: 'industry',
      title: '产业帮扶',
      icon: '🏭',
      stats: d?.industry
        ? [
            {
              label: '当年投入(万)',
              value: (d.industry.investment ?? 0).toFixed(2),
            },
          ]
        : [],
    },
    {
      key: 'infrastructure',
      title: '基础设施',
      icon: '🏗️',
      stats: d?.infrastructure
        ? [
            {
              label: '当年投入(万)',
              value: (d.infrastructure.investment ?? 0).toFixed(2),
            },
          ]
        : [],
    },
    {
      key: 'party_building',
      title: '党建帮扶',
      icon: '🏛️',
      stats: d?.['party-building']
        ? [
            {
              label: '投入(万)',
              value: (d['party-building'].investment ?? 0).toFixed(2),
            },
            {
              label: '联建活动(次)',
              value: d['party-building'].jointActivities ?? 0,
            },
          ]
        : [],
    },
    {
      key: 'medical',
      title: '医疗帮扶',
      icon: '🏥',
      stats: d?.medical
        ? [
            {
              label: '投入(万)',
              value: (d.medical.investment ?? 0).toFixed(2),
            },
            {
              label: '巡诊(人次)',
              value: d.medical.patientsServed ?? 0,
            },
          ]
        : [],
    },
    {
      key: 'consumption',
      title: '消费帮扶',
      icon: '🛒',
      stats: d?.consumption
        ? [
            {
              label: '采购产品(万)',
              value: (d.consumption.villageProductsPurchase ?? 0).toFixed(2),
            },
          ]
        : [],
    },
    {
      key: 'employment',
      title: '就业帮扶',
      icon: '💼',
      stats: d?.employment
        ? [
            {
              label: '聘用(人)',
              value: d.employment.hiredPopulation ?? 0,
            },
            {
              label: '培训(人次)',
              value: d.employment.trainedPopulation ?? 0,
            },
          ]
        : [],
    },
    {
      key: 'education',
      title: '教育帮扶',
      icon: '📚',
      stats: d?.education
        ? [
            {
              label: '投入(万)',
              value: (d.education.investment ?? 0).toFixed(2),
            },
            {
              label: '资助学生(人)',
              value: d.education.aidedStudents ?? 0,
            },
          ]
        : [],
    },
    {
      key: 'committee',
      title: '村委会情况',
      icon: '🏢',
      stats: (d as any)?.committee
        ? [
            {
              label: '成员数',
              value: (d as any).committee.members?.length ?? 0,
            },
            {
              label: '集体收入(万)',
              value: ((d as any).committee.collectiveIncomeAmount ?? 0).toFixed(2),
            },
          ]
        : [],
    },
  ]
})

async function loadAllData() {
  loading.value = true
  try {
    const _v = await getSupportedVillage(villageId.value)
    const village = unwrapData(_v)
    villageName.value = village.villageName
    const _raw = await getYearlyData(villageId.value, selectedYear.value)
    yearlyData.value = unwrapData(_raw)
  } catch (e: any) {
    ElMessage.error(e?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function openEditDialog(key: string) {
  editSectionKey.value = key
  editSectionTitle.value = sections.value.find((s) => s.key === key)?.title || ''
  editDialogVisible.value = true
}

async function handleDownloadTemplate(sectionKey: string) {
  try {
    await downloadTemplate(sectionKey, selectedYear.value)
    // 模板下载成功 — 浏览器已确认
  } catch {
    ElMessage.error('模板下载失败')
  }
}

async function handleImportSection(sectionKey: string, file: any) {
  const rawFile = file.raw || file
  try {
    const result = await importSectionData(villageId.value, selectedYear.value, sectionKey, rawFile)
    ElMessage.success(`导入成功 ${result.imported || result.rows || 0} 条`)
    if (result.failed > 0) {
      ElMessage.warning(`${result.failed} 条导入失败`)
    }
    loadAllData()
  } catch (e: any) {
    ElMessage.error(e?.message || '导入失败')
  }
}

async function handleDownloadAllTemplates() {
  downloadingAll.value = true
  try {
    await downloadAllTemplates(selectedYear.value)
    ElMessage.success('全部板块模板下载成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '模板下载失败')
  } finally {
    downloadingAll.value = false
  }
}

async function handleImportAll(file: any) {
  const rawFile = file.raw || file
  importingAll.value = true
  try {
    const result = await importAllSectionsData(villageId.value, selectedYear.value, rawFile)
    const secCount = result.sections?.length || result.sheets || 0
    ElMessage.success(
      `全部导入完成：成功 ${result.imported || result.rows || 0} 条（${secCount} 个板块）`
    )
    if (result.failed > 0) {
      ElMessage.warning(`${result.failed} 条数据导入失败`)
    }
    loadAllData()
  } catch (e: any) {
    ElMessage.error(e?.message || '全部导入失败')
  } finally {
    importingAll.value = false
  }
}

function handleBack() {
  pushSafe(`/supported-villages/${villageId.value}`)
}

onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.yearly-overview-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1b4332;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.section-card {
  background: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.section-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.section-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.section-card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1b4332;
}

.section-icon {
  font-size: 20px;
}

.section-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
  min-height: 48px;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #40916c;
}

.summary-label {
  font-size: 12px;
  color: #999;
}

.no-data-hint {
  color: #bbb;
  font-size: 13px;
  display: flex;
  align-items: center;
}

.section-card-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.inline-upload {
  display: inline-block;
}
</style>
