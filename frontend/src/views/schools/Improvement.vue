<template>
  <div class="school-improvement">
    <el-page-header title="返回" @back="goBack">
      <template #content>
        <span class="page-title">学校改善展示</span>
      </template>
    </el-page-header>

    <el-card class="main-card" shadow="never">
      <!-- 学校信息 -->
      <div class="school-header">
        <h2>{{ schoolData.name }}</h2>
        <el-descriptions :column="4" border>
          <el-descriptions-item label="学校类型">{{ schoolData.type }}</el-descriptions-item>
          <el-descriptions-item label="学生人数"
            >{{ schoolData.studentCount }}人</el-descriptions-item
          >
          <el-descriptions-item label="教师人数"
            >{{ schoolData.teacherCount }}人</el-descriptions-item
          >
          <el-descriptions-item label="班级数">{{ schoolData.classCount }}个</el-descriptions-item>
          <el-descriptions-item label="帮扶单位" :span="2">{{
            schoolData.supportUnit
          }}</el-descriptions-item>
          <el-descriptions-item label="帮扶金额"
            >{{ schoolData.supportAmount }}万元</el-descriptions-item
          >
          <el-descriptions-item label="帮扶时间">{{ schoolData.supportDate }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 改善项目展示 -->
      <el-tabs v-model="activeCategory" class="improvement-tabs">
        <el-tab-pane label="教学设施" name="teaching">
          <div class="improvement-section">
            <div
              v-for="item in getItemsByCategory('teaching')"
              :key="item.id"
              class="improvement-card"
            >
              <el-card shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span>{{ item.title }}</span>
                    <el-tag :type="item.status === '已完成' ? 'success' : 'primary'">
                      {{ item.status }}
                    </el-tag>
                  </div>
                </template>
                <ImageComparison
                  :before-image="item.beforeImage"
                  :after-image="item.afterImage"
                  :before-label="item.beforeLabel"
                  :after-label="item.afterLabel"
                  :before-date="item.beforeDate"
                  :after-date="item.afterDate"
                  :description="item.description"
                  :show-info="true"
                />
                <div class="improvement-stats">
                  <el-row :gutter="12">
                    <el-col v-for="stat in item.stats" :key="stat.label" :span="8">
                      <div class="stat-box">
                        <div class="stat-value">{{ stat.value }}</div>
                        <div class="stat-label">{{ stat.label }}</div>
                      </div>
                    </el-col>
                  </el-row>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="生活设施" name="living">
          <div class="improvement-section">
            <div
              v-for="item in getItemsByCategory('living')"
              :key="item.id"
              class="improvement-card"
            >
              <el-card shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span>{{ item.title }}</span>
                    <el-tag :type="item.status === '已完成' ? 'success' : 'primary'">
                      {{ item.status }}
                    </el-tag>
                  </div>
                </template>
                <BeforeAfterSlider
                  :before-image="item.beforeImage"
                  :after-image="item.afterImage"
                  :before-label="item.beforeLabel"
                  :after-label="item.afterLabel"
                  :show-controls="true"
                />
                <p class="description">{{ item.description }}</p>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="运动设施" name="sports">
          <div class="improvement-section">
            <div
              v-for="item in getItemsByCategory('sports')"
              :key="item.id"
              class="improvement-card"
            >
              <el-card shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span>{{ item.title }}</span>
                    <el-tag :type="item.status === '已完成' ? 'success' : 'primary'">
                      {{ item.status }}
                    </el-tag>
                  </div>
                </template>
                <ImageComparison
                  :before-image="item.beforeImage"
                  :after-image="item.afterImage"
                  :before-label="item.beforeLabel"
                  :after-label="item.afterLabel"
                  :show-info="false"
                />
                <p class="description">{{ item.description }}</p>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="全部记录" name="all">
          <GalleryView :images="allGalleryImages" />
        </el-tab-pane>
      </el-tabs>

      <!-- 改善总结 -->
      <el-divider content-position="left">
        <h3>改善成果总结</h3>
      </el-divider>

      <el-row :gutter="20">
        <el-col v-for="summary in summaryData" :key="summary.label" :span="6">
          <el-card shadow="hover" class="summary-card">
            <el-statistic
              :title="summary.label"
              :value="summary.value"
              :suffix="summary.suffix"
              :precision="summary.precision"
            />
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import ImageComparison from '@/components/business/ImageComparison.vue'
import BeforeAfterSlider from '@/components/business/BeforeAfterSlider.vue'
import GalleryView from '@/components/business/GalleryView.vue'

const router = useRouter()

const activeCategory = ref('teaching')

const schoolData = ref({
  name: '希望小学',
  type: '小学',
  studentCount: 320,
  teacherCount: 18,
  classCount: 12,
  supportUnit: '某军区政治工作部',
  supportAmount: 50,
  supportDate: '2020年9月',
})

interface ImprovementItem {
  id: number
  category: string
  title: string
  beforeImage: string
  afterImage: string
  beforeLabel: string
  afterLabel: string
  beforeDate?: string
  afterDate?: string
  description: string
  status: string
  stats?: Array<{ label: string; value: string }>
}

const improvementItems = ref<ImprovementItem[]>([
  {
    id: 1,
    category: 'teaching',
    title: '多媒体教室改造',
    beforeImage: '/images/school/classroom_before.jpg',
    afterImage: '/images/school/classroom_after.jpg',
    beforeLabel: '改造前',
    afterLabel: '改造后',
    beforeDate: '2020-09-01',
    afterDate: '2024-03-15',
    description: '安装智能黑板、投影设备、电脑等现代化教学设备，提升教学质量',
    status: '已完成',
    stats: [
      { label: '教室数量', value: '6间' },
      { label: '投入金额', value: '15万' },
      { label: '受益学生', value: '180人' },
    ],
  },
  {
    id: 2,
    category: 'teaching',
    title: '图书室扩建',
    beforeImage: '/images/school/library_before.jpg',
    afterImage: '/images/school/library_after.jpg',
    beforeLabel: '扩建前',
    afterLabel: '扩建后',
    beforeDate: '2020-09-01',
    afterDate: '2024-05-20',
    description: '图书室面积扩大一倍，新增图书5000册，配备电子阅读设备',
    status: '已完成',
    stats: [
      { label: '图书数量', value: '8000册' },
      { label: '阅读座位', value: '80个' },
      { label: '投入金额', value: '12万' },
    ],
  },
  {
    id: 3,
    category: 'living',
    title: '学生宿舍改善',
    beforeImage: '/images/school/dormitory_before.jpg',
    afterImage: '/images/school/dormitory_after.jpg',
    beforeLabel: '改善前',
    afterLabel: '改善后',
    description: '改善住宿条件，配备新床铺、储物柜、空调等设施',
    status: '已完成',
  },
  {
    id: 4,
    category: 'living',
    title: '食堂升级改造',
    beforeImage: '/images/school/canteen_before.jpg',
    afterImage: '/images/school/canteen_after.jpg',
    beforeLabel: '改造前',
    afterLabel: '改造后',
    description: '扩建食堂面积，更新厨房设备，改善就餐环境',
    status: '已完成',
  },
  {
    id: 5,
    category: 'sports',
    title: '运动场改造',
    beforeImage: '/images/school/playground_before.jpg',
    afterImage: '/images/school/playground_after.jpg',
    beforeLabel: '改造前',
    afterLabel: '改造后',
    description: '土操场改造为塑胶跑道和人工草坪足球场',
    status: '已完成',
  },
  {
    id: 6,
    category: 'sports',
    title: '体育器材配备',
    beforeImage: '/images/school/equipment_before.jpg',
    afterImage: '/images/school/equipment_after.jpg',
    beforeLabel: '配备前',
    afterLabel: '配备后',
    description: '新增篮球架、乒乓球台、单双杠等体育器材',
    status: '已完成',
  },
])

const summaryData = ref([
  { label: '改善项目', value: 12, suffix: '个', precision: 0 },
  { label: '投入金额', value: 50, suffix: '万元', precision: 0 },
  { label: '受益学生', value: 320, suffix: '人', precision: 0 },
  { label: '满意度', value: 98.5, suffix: '%', precision: 1 },
])

const getItemsByCategory = (category: string) => {
  return improvementItems.value.filter((item) => item.category === category)
}

const allGalleryImages = computed(() => {
  const images: any[] = []
  improvementItems.value.forEach((item) => {
    images.push({
      id: `${item.id}_before`,
      url: item.beforeImage,
      title: `${item.title} - ${item.beforeLabel}`,
      date: item.beforeDate,
      description: item.description,
    })
    images.push({
      id: `${item.id}_after`,
      url: item.afterImage,
      title: `${item.title} - ${item.afterLabel}`,
      date: item.afterDate,
      description: item.description,
    })
  })
  return images
})

const goBack = () => {
  router.back()
}
</script>

<style scoped lang="scss">
.school-improvement {
  padding: 20px;

  .page-title {
    font-size: 18px;
    font-weight: 600;
  }

  .main-card {
    margin-top: 20px;

    .school-header {
      margin-bottom: 30px;

      h2 {
        margin: 0 0 20px 0;
        font-size: 24px;
        color: #303133;
      }
    }

    .improvement-tabs {
      margin-top: 30px;

      .improvement-section {
        padding: 20px 0;

        .improvement-card {
          margin-bottom: 30px;

          &:last-child {
            margin-bottom: 0;
          }

          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: 600;
          }

          .description {
            margin-top: 16px;
            font-size: 14px;
            color: #606266;
            line-height: 1.6;
          }

          .improvement-stats {
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e4e7ed;

            .stat-box {
              text-align: center;

              .stat-value {
                font-size: 20px;
                font-weight: 600;
                color: #409eff;
                margin-bottom: 4px;
              }

              .stat-label {
                font-size: 12px;
                color: #909399;
              }
            }
          }
        }
      }
    }

    .summary-card {
      text-align: center;

      :deep(.el-statistic__head) {
        font-size: 14px;
        color: #909399;
      }

      :deep(.el-statistic__content) {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
      }
    }
  }
}
</style>
