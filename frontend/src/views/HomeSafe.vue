<template>
  <div class="dashboard-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <h2 class="welcome-title">欢迎回来，{{ authStore.user?.name || userRoleName }}</h2>
        <p class="welcome-date">{{ currentDate }}</p>
        <p v-if="dashStats" class="welcome-summary">
          当前共有 <strong>{{ dashStats.total_projects }}</strong> 个帮扶项目， 覆盖
          <strong>{{ dashStats.total_villages }}</strong> 个帮扶村、
          <strong>{{ dashStats.total_schools }}</strong> 所学校， 惠及
          <strong>{{ (dashStats.total_population || 0).toLocaleString() }}</strong>
          人
        </p>
      </div>
      <QuickActions
        :is-manager="isManagerRole"
        :is-admin="isAdminRole"
        :backing-up="backingUp"
        @backup="handleOneKeyBackup"
        @restore="showRestoreDialog = true"
        @toggle-layout="showLayoutEditor = !showLayoutEditor"
      />
    </div>

    <!-- 布局编辑器面板 -->
    <div v-if="showLayoutEditor" class="layout-editor-panel">
      <div class="layout-editor-header">
        <span>⚙️ 自定义工作台布局</span>
        <button class="layout-close-btn" @click="showLayoutEditor = false">✕</button>
      </div>
      <!-- 预设布局 -->
      <div class="layout-presets">
        <span class="presets-label">快速布局：</span>
        <el-button
          v-for="preset in LAYOUT_PRESETS"
          :key="preset.key"
          size="small"
          :type="currentPreset === preset.key ? 'primary' : ''"
          @click="applyPreset(preset.key)"
        >
          {{ preset.label }}
        </el-button>
      </div>
      <!-- 可拖拽排序的卡片列表 -->
      <div class="layout-editor-body">
        <div
          v-for="(card, index) in orderedCards"
          :key="card.key"
          class="layout-editor-item"
          :class="{ 'item-disabled': !cardVisibility[card.key] }"
          draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event, index)"
          @dragend="onDragEnd"
          @drop.prevent="onDrop($event, index)"
        >
          <span class="drag-handle">⠿</span>
          <span class="item-order">{{ index + 1 }}</span>
          <el-switch
            :model-value="cardVisibility[card.key]"
            size="small"
            @change="
              (val: any) => {
                cardVisibility[card.key] = !!val
              }
            "
          />
          <div class="item-info">
            <span class="item-label">{{ card.label }}</span>
            <span class="item-desc">{{ card.description }}</span>
          </div>
        </div>
      </div>
      <div class="layout-editor-footer">
        <span class="layout-status">
          已显示 {{ visibleCount }} / {{ DASHBOARD_CARDS.length }} 个面板
        </span>
        <button class="layout-reset-btn" @click="resetLayout">恢复默认布局</button>
      </div>
    </div>

    <!-- 恢复数据弹窗 -->
    <div v-if="showRestoreDialog" class="modal-overlay" @click.self="showRestoreDialog = false">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>🔄 恢复数据</h3>
          <button class="modal-close" @click="showRestoreDialog = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="restore-section">
            <h4>从已有备份恢复</h4>
            <div v-if="restoreBackups.length === 0" class="empty-tip">暂无备份文件</div>
            <div v-else class="backup-list">
              <div v-for="backup in restoreBackups" :key="backup.filename" class="backup-item">
                <div class="backup-info">
                  <span class="backup-name">{{ backup.filename }}</span>
                  <span class="backup-meta"
                    >{{ formatBackupSize(backup.size) }} ·
                    {{ formatBackupTime(backup.created_at) }}</span
                  >
                </div>
                <button
                  class="btn-sm restore-btn"
                  :disabled="restoring"
                  @click="restoreFromBackup(backup.filename)"
                >
                  {{ restoring ? '恢复中...' : '恢复' }}
                </button>
              </div>
            </div>
          </div>
          <div class="restore-section">
            <h4>上传备份文件恢复</h4>
            <div class="upload-area">
              <input
                ref="restoreFileInput"
                type="file"
                accept=".db,.bak,.gz"
                style="display: none"
                @change="handleUploadRestore"
              />
              <button
                class="action-btn secondary"
                :disabled="restoring"
                @click="($refs.restoreFileInput as HTMLInputElement)?.click()"
              >
                📁 选择备份文件上传并恢复
              </button>
              <p class="upload-hint">支持 .db / .bak / .db.gz 格式</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 核心统计指标 -->
    <div v-show="cardVisibility.stats" class="stats-section">
      <div v-if="!dashLoading && coreStats.length > 0" class="stats-grid">
        <div
          v-for="stat in coreStats"
          :key="stat.label"
          class="stat-card"
          @click="stat.path && pushSafe(stat.path)"
        >
          <div class="stat-icon-wrapper" :style="{ backgroundColor: stat.bgColor }">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <span class="stat-icon" v-html="stat.icon"></span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
          <div v-if="stat.extra" class="stat-extra">
            <span class="stat-extra-text">{{ stat.extra }}</span>
          </div>
        </div>
        <div class="stat-refresh" title="刷新统计数据" @click="refreshDashboard">
          <span :class="{ refreshing: dashRefreshing }">🔄</span>
        </div>
      </div>
      <div v-else-if="!dashLoading && coreStats.length === 0" class="empty-state">
        <div class="empty-icon">📊</div>
        <div class="empty-text">暂无统计数据</div>
        <div class="empty-hint">请先添加帮扶项目、村庄或学校数据</div>
        <button class="action-btn primary" @click="pushSafe('/projects')">
          <span class="btn-icon">+</span> 创建第一个项目
        </button>
      </div>
      <div v-else class="stats-grid">
        <div v-for="i in 4" :key="i" class="stat-card skeleton-card">
          <div class="skeleton-icon"></div>
          <div class="skeleton-text-group">
            <div class="skeleton-line wide"></div>
            <div class="skeleton-line narrow"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷导航 -->
    <div v-show="cardVisibility.quickNav" class="section-card">
      <div class="section-header">
        <h3>⚡ 快捷导航</h3>
      </div>
      <div class="nav-grid">
        <div v-for="nav in quickNavItems" :key="nav.path" class="nav-item" @click="navigateTo(nav)">
          <span class="nav-icon">{{ nav.icon }}</span>
          <span class="nav-label">{{ nav.label }}</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-grid">
      <!-- 左列 -->
      <div class="left-col">
        <!-- 项目进度 -->
        <div v-show="cardVisibility.projects" class="section-card">
          <div class="section-header">
            <h3>📌 项目进度</h3>
            <button class="text-btn" @click="pushSafe('/projects')">查看全部 ›</button>
          </div>
          <div class="section-body">
            <div v-if="dashLoading" class="skeleton-table">
              <div v-for="i in 3" :key="i" class="skeleton-row">
                <div class="skeleton-line wide"></div>
                <div class="skeleton-line narrow"></div>
              </div>
            </div>
            <template v-else-if="recentProjects.length > 0">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>项目名称</th>
                    <th>类型</th>
                    <th>状态</th>
                    <th style="width: 140px">进度</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="project in recentProjects" :key="project.id">
                    <td class="project-name" @click="pushSafe(`/projects/${project.id}`)">
                      {{ project.name }}
                    </td>
                    <td>
                      <span class="type-tag">{{ translateType(project.type) }}</span>
                    </td>
                    <td>
                      <span class="status-badge" :class="getStatusClass(project.status)">
                        {{ translateStatus(project.status) }}
                      </span>
                    </td>
                    <td>
                      <div class="progress-inline">
                        <div class="progress-bar-bg">
                          <div
                            class="progress-bar-fill"
                            :style="{
                              width: project.progress + '%',
                              backgroundColor: getProgressColor(project.progress),
                            }"
                          ></div>
                        </div>
                        <span class="progress-text">{{ project.progress }}%</span>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </template>
            <div v-else class="empty-state">暂无项目数据</div>
          </div>
        </div>

        <!-- 经费概况 -->
        <div v-show="cardVisibility.funds" class="section-card">
          <div class="section-header">
            <h3>💰 经费概况</h3>
            <button class="text-btn" @click="pushSafe('/funds')">查看全部 ›</button>
          </div>
          <div class="section-body">
            <div class="fund-summary-row">
              <div class="fund-summary-item">
                <div class="fund-label">经费总额</div>
                <div class="fund-value">
                  {{ dashStats?.total_funds || 0 }}
                  <span class="fund-unit">万元</span>
                </div>
              </div>
              <div class="fund-summary-item">
                <div class="fund-label">已拨付</div>
                <div class="fund-value text-green">
                  {{ dashStats?.funds_allocated || 0 }}
                  <span class="fund-unit">万元</span>
                </div>
              </div>
              <div class="fund-summary-item">
                <div class="fund-label">待审批</div>
                <div class="fund-value text-orange">
                  {{ dashStats?.funds_pending || 0 }}
                  <span class="fund-unit">万元</span>
                </div>
              </div>
              <div class="fund-summary-item">
                <div class="fund-label">规划中</div>
                <div class="fund-value text-blue">
                  {{ dashStats?.funds_planned || 0 }}
                  <span class="fund-unit">万元</span>
                </div>
              </div>
            </div>
            <div v-if="dashStats?.total_funds" class="fund-progress-bar">
              <div class="fund-bar-allocated" :style="{ width: fundAllocatedPercent + '%' }"></div>
              <div class="fund-bar-pending" :style="{ width: fundPendingPercent + '%' }"></div>
              <div class="fund-bar-planned" :style="{ width: fundPlannedPercent + '%' }"></div>
            </div>
            <div class="fund-legend">
              <span class="legend-item"><i class="legend-dot green"></i>已拨付</span>
              <span class="legend-item"><i class="legend-dot orange"></i>待审批</span>
              <span class="legend-item"><i class="legend-dot blue"></i>规划中</span>
            </div>
          </div>
        </div>

        <!-- 近期动态 -->
        <div v-show="cardVisibility.activities" class="section-card">
          <div class="section-header">
            <h3>🕐 近期动态</h3>
            <button class="text-btn" @click="showActivityForm = !showActivityForm">
              {{ showActivityForm ? '取消' : '+ 添加动态' }}
            </button>
          </div>
          <div class="section-body">
            <!-- 添加动态表单 -->
            <div v-if="showActivityForm" class="activity-add-form">
              <div class="activity-form-row">
                <select v-model="newActivity.type" class="activity-select">
                  <option value="project">项目</option>
                  <option value="fund">经费</option>
                  <option value="import">导入</option>
                  <option value="school">学校</option>
                  <option value="village">帮扶村</option>
                  <option value="policy">政策</option>
                </select>
                <input
                  v-model="newActivity.action"
                  class="activity-input"
                  placeholder="操作（如：新增、更新）"
                />
                <input
                  v-model="newActivity.target"
                  class="activity-input activity-input-wide"
                  placeholder="目标（如：XX帮扶项目）"
                />
                <button
                  class="activity-add-btn"
                  :disabled="!newActivity.action.trim() || !newActivity.target.trim()"
                  @click="addActivity"
                >
                  添加
                </button>
              </div>
            </div>
            <div class="activity-list">
              <div v-for="act in recentActivities" :key="act.id" class="activity-item">
                <div class="activity-dot" :class="'dot-' + act.type"></div>
                <!-- 编辑模式 -->
                <template v-if="editingActivityId === act.id">
                  <div class="activity-edit-form">
                    <select v-model="editingActivity.type" class="activity-select-sm">
                      <option value="project">项目</option>
                      <option value="fund">经费</option>
                      <option value="import">导入</option>
                      <option value="school">学校</option>
                      <option value="village">帮扶村</option>
                      <option value="policy">政策</option>
                    </select>
                    <input
                      v-model="editingActivity.action"
                      class="activity-input-sm"
                      placeholder="操作"
                    />
                    <input
                      v-model="editingActivity.target"
                      class="activity-input-sm activity-input-wide"
                      placeholder="目标"
                    />
                    <button
                      class="activity-save-btn"
                      :disabled="!editingActivity.action.trim() || !editingActivity.target.trim()"
                      @click="saveActivity(act.id)"
                    >
                      保存
                    </button>
                    <button class="activity-cancel-btn" @click="cancelEditActivity">取消</button>
                  </div>
                </template>
                <!-- 显示模式 -->
                <template v-else>
                  <div class="activity-content">
                    <span class="activity-action">{{ act.action }}</span>
                    <span class="activity-target">{{ act.target }}</span>
                  </div>
                  <div class="activity-meta">
                    <span class="activity-user">{{ act.user }}</span>
                    <span class="activity-time">{{ act.time }}</span>
                  </div>
                  <div class="activity-actions">
                    <button class="activity-edit-btn" title="编辑" @click="startEditActivity(act)">
                      ✎
                    </button>
                    <button
                      class="activity-delete-btn"
                      title="删除"
                      @click="deleteActivity(act.id)"
                    >
                      ✕
                    </button>
                  </div>
                </template>
              </div>
              <div v-if="recentActivities.length === 0" class="activity-empty">暂无近期动态</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右列 -->
      <div class="right-col">
        <!-- 待办事项 -->
        <div v-show="cardVisibility.todos" class="section-card">
          <div class="section-header">
            <h3>📝 待办事项</h3>
            <span v-if="pendingTodos > 0" class="badge-count">{{ pendingTodos }}</span>
          </div>
          <div class="section-body">
            <div class="task-add-row">
              <input
                v-model="newTaskTitle"
                class="task-input"
                placeholder="输入新的待办事项..."
                @keyup.enter="addTask"
              />
              <select v-model="newTaskPriority" class="task-priority-select">
                <option value="high">紧急</option>
                <option value="medium">重要</option>
                <option value="low">普通</option>
              </select>
              <button class="task-add-btn" :disabled="!newTaskTitle.trim()" @click="addTask">
                添加
              </button>
            </div>
            <div class="task-list">
              <div v-for="task in tasks" :key="task.id" class="task-item">
                <label class="checkbox-wrapper">
                  <input type="checkbox" :checked="task.completed" @change="toggleTask(task.id)" />
                  <span class="checkmark"></span>
                  <span class="task-text" :class="{ done: task.completed }">{{ task.title }}</span>
                </label>
                <div class="task-actions">
                  <span class="priority-tag" :class="task.priority">{{ task.priorityText }}</span>
                  <button class="task-delete-btn" title="删除" @click="removeTask(task.id)">
                    ✕
                  </button>
                </div>
              </div>
              <div v-if="tasks.length === 0" class="task-empty">暂无待办事项</div>
            </div>
          </div>
        </div>

        <!-- 帮扶数据概览 -->
        <div v-show="cardVisibility.dataOverview" class="section-card">
          <div class="section-header">
            <h3>📊 数据概览</h3>
          </div>
          <div class="section-body">
            <div class="data-overview-list">
              <div class="data-overview-item">
                <span class="do-label">帮扶村人口</span>
                <span class="do-value"
                  >{{ (dashStats?.total_population || 0).toLocaleString() }} 人</span
                >
              </div>
              <div class="data-overview-item">
                <span class="do-label">帮扶村户数</span>
                <span class="do-value"
                  >{{ (dashStats?.total_households || 0).toLocaleString() }} 户</span
                >
              </div>
              <div class="data-overview-item">
                <span class="do-label">在校学生</span>
                <span class="do-value"
                  >{{ (dashStats?.total_students || 0).toLocaleString() }} 人</span
                >
              </div>
              <div class="data-overview-item">
                <span class="do-label">师资力量</span>
                <span class="do-value">{{ dashStats?.total_teachers || 0 }} 人</span>
              </div>
              <div class="data-overview-item">
                <span class="do-label">数据完整度</span>
                <span class="do-value">
                  <span class="completeness-bar">
                    <span
                      class="completeness-fill"
                      :style="{
                        width: (dashStats?.data_completeness || 0) * 100 + '%',
                      }"
                    ></span>
                  </span>
                  {{ ((dashStats?.data_completeness || 0) * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="data-overview-item">
                <span class="do-label">待审批</span>
                <span class="do-value text-orange">{{ dashStats?.pending_approvals || 0 }} 条</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { logger } from '@/utils/logger'

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import QuickActions from '@/views/dashboard/components/QuickActions.vue'
import { useRouterSafe } from '@/composables/useRouterSafe'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/request'
import { useOnboarding } from '@/composables/useOnboarding'
import { ElMessage, ElMessageBox } from 'element-plus'
import { enhancedStorage, STORAGE_KEYS } from '@/utils/enhancedStorage'

// 新手引导（首次访问时自动展示）
const { startTour: _startTour } = useOnboarding()
void _startTour // 保留引用供后续使用

const { pushSafe } = useRouterSafe()
const authStore = useAuthStore()

const backingUp = ref(false)
const showRestoreDialog = ref(false)

// ─── 仪表板布局个性化 ───
const DASHBOARD_CARDS = [
  {
    key: 'stats',
    label: '核心统计指标',
    description: '项目数、村庄数、学校数、人口等关键数字',
  },
  { key: 'quickNav', label: '快捷导航', description: '常用功能快捷入口按钮组' },
  { key: 'projects', label: '项目进度', description: '帮扶项目列表与完成进度' },
  { key: 'funds', label: '经费概况', description: '经费分配与使用情况概览' },
  {
    key: 'activities',
    label: '近期动态',
    description: '最新帮扶活动与工作动态',
  },
  { key: 'todos', label: '待办事项', description: '待审批、待处理的工作任务' },
  {
    key: 'dataOverview',
    label: '数据概览',
    description: '年度帮扶数据汇总统计',
  },
] as const
type CardKey = (typeof DASHBOARD_CARDS)[number]['key']
const DEFAULT_CARD_VISIBILITY = Object.fromEntries(
  DASHBOARD_CARDS.map((c) => [c.key, true])
) as Record<CardKey, boolean>

const cardVisibility = ref<Record<CardKey, boolean>>({
  ...DEFAULT_CARD_VISIBILITY,
  ...(enhancedStorage.get<Partial<Record<CardKey, boolean>>>(STORAGE_KEYS.DASHBOARD_LAYOUT) ?? {}),
})
const showLayoutEditor = ref(false)

watch(
  cardVisibility,
  (v) => {
    enhancedStorage.set(STORAGE_KEYS.DASHBOARD_LAYOUT, v)
  },
  { deep: true }
)

function resetLayout() {
  cardVisibility.value = { ...DEFAULT_CARD_VISIBILITY }
  orderedCards.value = [...DASHBOARD_CARDS]
  currentPreset.value = 'default'
  enhancedStorage.remove(STORAGE_KEYS.DASHBOARD_ORDER)
}

// ── 布局预设 ──
const LAYOUT_PRESETS = [
  { key: 'all', label: '全部显示' },
  { key: 'manager', label: '管理员视角' },
  { key: 'operator', label: '操作员视角' },
  { key: 'minimal', label: '简约模式' },
] as const
type PresetKey = (typeof LAYOUT_PRESETS)[number]['key']
const currentPreset = ref<PresetKey | 'default'>('default')

const visibleCount = computed(() => Object.values(cardVisibility.value).filter(Boolean).length)

function applyPreset(key: PresetKey) {
  currentPreset.value = key
  const allKeys = DASHBOARD_CARDS.map((c) => c.key)
  const reset: Record<string, boolean> = {}
  switch (key) {
    case 'all':
      allKeys.forEach((k) => (reset[k] = true))
      break
    case 'manager':
      // 管理员：全部显示
      allKeys.forEach((k) => (reset[k] = true))
      break
    case 'operator':
      // 操作员：隐藏数据概览、待办事项
      allKeys.forEach((k) => (reset[k] = k !== 'dataOverview' && k !== 'todos'))
      break
    case 'minimal':
      // 简约：仅核心统计 + 快捷导航 + 项目进度
      allKeys.forEach((k) => (reset[k] = ['stats', 'quickNav', 'projects'].includes(k)))
      break
  }
  cardVisibility.value = reset as Record<CardKey, boolean>
}

// ── 拖拽排序 ──
const savedOrder = enhancedStorage.get<CardKey[]>(STORAGE_KEYS.DASHBOARD_ORDER)
const orderedCards = ref<(typeof DASHBOARD_CARDS)[number][]>(
  (() => {
    if (!savedOrder) return [...DASHBOARD_CARDS]
    // 以保存的顺序为基准，追加新增卡片（避免新卡片被静默丢弃）
    const savedKeys = new Set(savedOrder)
    const merged = savedOrder
      .map((k) => DASHBOARD_CARDS.find((c) => c.key === k))
      .filter(Boolean) as (typeof DASHBOARD_CARDS)[number][]
    // 追加未在保存顺序中的新卡片
    for (const card of DASHBOARD_CARDS) {
      if (!savedKeys.has(card.key)) merged.push(card)
    }
    return merged
  })()
)

let dragIndex = -1

function onDragStart(_e: DragEvent, index: number) {
  dragIndex = index
}

function onDragOver(_e: DragEvent, index: number) {
  if (dragIndex === -1 || dragIndex === index) return
  const items = [...orderedCards.value]
  const [moved] = items.splice(dragIndex, 1)
  items.splice(index, 0, moved)
  orderedCards.value = items
  dragIndex = index
}

function onDrop(_e: DragEvent, _index: number) {
  dragIndex = -1
  // 持久化顺序
  enhancedStorage.set(
    STORAGE_KEYS.DASHBOARD_ORDER,
    orderedCards.value.map((c) => c.key)
  )
}

function onDragEnd() {
  dragIndex = -1
}

const restoreBackups = ref<any[]>([])
const restoring = ref(false)
// const restoreFileInput = ref<HTMLInputElement | null>(null);
const messages = ref<any[]>([])

const dashLoading = ref(true)
const dashRefreshing = ref(false)
const dashStats = ref<any>(null)
const recentProjects = ref<any[]>([])
const recentActivities = ref<any[]>([])

// 近期动态编辑状态
const showActivityForm = ref(false)
const newActivity = ref({ type: 'project', action: '', target: '' })
const editingActivityId = ref<number | string | null>(null)
const editingActivity = ref({ type: '', action: '', target: '' })

const priorityTextMap: Record<string, string> = {
  high: '紧急',
  medium: '重要',
  low: '普通',
}

const tasks = ref<any[]>([])
const newTaskTitle = ref('')
const newTaskPriority = ref('medium')
const tasksLoading = ref(false)

const pendingTodos = computed(() => tasks.value.filter((t: any) => !t.completed).length)

function mapTaskItem(item: any) {
  return {
    ...item,
    priorityText: priorityTextMap[item.priority] || '普通',
  }
}

async function loadTasks() {
  tasksLoading.value = true
  try {
    const res = await request.get('/todos', {
      params: { page: 1, page_size: 50 },
      showError: false,
    } as any)
    const data = res.data?.data || res.data
    const items = data?.items || (Array.isArray(data) ? data : [])
    tasks.value = items.map(mapTaskItem)
  } catch (e) {
    logger.error('加载待办失败:', e)
    tasks.value = []
  } finally {
    tasksLoading.value = false
  }
}

async function addTask() {
  const title = newTaskTitle.value.trim()
  if (!title) return
  try {
    const res = await request.post('/todos', {
      title,
      priority: newTaskPriority.value,
    })
    const created = res.data?.data || res.data
    if (created?.id) {
      tasks.value.unshift(mapTaskItem(created))
    } else {
      await loadTasks()
    }
    newTaskTitle.value = ''
  } catch (e: any) {
    logger.error('添加待办失败:', e)
    ElMessage.error('添加待办失败: ' + (e?.response?.data?.detail || e.message))
  }
}

async function toggleTask(id: number) {
  const task = tasks.value.find((t: any) => t.id === id)
  if (!task) return
  try {
    const res = await request.patch(`/todos/${id}/toggle`)
    const updated = res.data?.data || res.data
    if (updated) {
      task.completed = updated.completed
    } else {
      task.completed = !task.completed
    }
  } catch (e) {
    logger.error('切换待办状态失败:', e)
  }
}

async function removeTask(id: number) {
  try {
    await request.delete(`/todos/${id}`)
    tasks.value = tasks.value.filter((t: any) => t.id !== id)
  } catch (e) {
    logger.error('删除待办失败:', e)
  }
}

// 近期动态 CRUD
async function addActivity() {
  const { type, action, target } = newActivity.value
  if (!action.trim() || !target.trim()) return
  try {
    const res = await request.post('/dashboard/recent-activities', {
      type,
      action: action.trim(),
      target: target.trim(),
    })
    const created = res.data
    if (created?.id) {
      recentActivities.value.unshift(created)
    } else {
      await reloadActivities()
    }
    newActivity.value = { type: 'project', action: '', target: '' }
    showActivityForm.value = false
  } catch (e: any) {
    logger.error('添加动态失败:', e)
    ElMessage.error('添加动态失败: ' + (e?.response?.data?.detail || e.message))
  }
}

function startEditActivity(act: any) {
  editingActivityId.value = act.id
  editingActivity.value = {
    type: act.type,
    action: act.action,
    target: act.target,
  }
}

function cancelEditActivity() {
  editingActivityId.value = null
  editingActivity.value = { type: '', action: '', target: '' }
}

async function saveActivity(id: number | string) {
  const { type, action, target } = editingActivity.value
  if (!action.trim() || !target.trim()) return
  try {
    const res = await request.put(`/dashboard/recent-activities/${id}`, {
      type,
      action: action.trim(),
      target: target.trim(),
    })
    const updated = res.data
    const idx = recentActivities.value.findIndex((a: any) => String(a.id) === String(id))
    if (idx !== -1) {
      recentActivities.value[idx] = {
        ...recentActivities.value[idx],
        ...updated,
        type,
        action: action.trim(),
        target: target.trim(),
      }
    }
    cancelEditActivity()
  } catch (e: any) {
    logger.error('更新动态失败:', e)
    // 即使API失败，也进行本地更新
    const idx = recentActivities.value.findIndex((a: any) => String(a.id) === String(id))
    if (idx !== -1) {
      recentActivities.value[idx] = {
        ...recentActivities.value[idx],
        type,
        action: action.trim(),
        target: target.trim(),
      }
    }
    cancelEditActivity()
  }
}

async function deleteActivity(id: number | string) {
  try {
    await ElMessageBox.confirm('确定删除这条动态吗？', '确认删除', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await request.delete(`/dashboard/recent-activities/${id}`)
    // 使用宽松比较确保 string/number id 都能匹配
    recentActivities.value = recentActivities.value.filter((a: any) => String(a.id) !== String(id))
  } catch (e: any) {
    logger.error('删除动态失败:', e)
    // 即使API调用失败，也从本地列表中移除（前端优先更新）
    recentActivities.value = recentActivities.value.filter((a: any) => String(a.id) !== String(id))
  }
}

async function reloadActivities() {
  try {
    const res = await request.get('/dashboard/recent-activities', {
      showError: false,
    } as any)
    const d = res.data
    recentActivities.value = (d?.items || (Array.isArray(d) ? d : [])).slice(0, 8)
  } catch {
    logger.error('加载动态失败')
  }
}

const userRole = computed(() => authStore.user?.role || 'viewer')
const isAdminRole = computed(() => ['admin', 'super_admin'].includes(userRole.value))
const isManagerRole = computed(() => ['admin', 'super_admin', 'manager'].includes(userRole.value))

const userRoleName = computed(() => {
  const roleMap: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '系统管理员',
    approval_leader: '审批领导',
    manager: '管理人员',
    operator: '操作员',
    viewer: '查看者',
  }
  return roleMap[userRole.value] || '用户'
})

// ─── 快捷导航类型定义 ───
interface NavItem {
  icon: string
  label: string
  path: string
  /** 需要的角色，空数组表示所有人可见 */
  roles?: string[]
  /** 是否需要管理员权限 */
  requiresAdmin?: boolean
}

// 公共快捷导航项（所有人可见）
const commonNavItems: NavItem[] = [
  { icon: '📁', label: '帮扶项目', path: '/projects', roles: [] },
  { icon: '🏨️', label: '帮扶村', path: '/villages', roles: [] },
  { icon: '🏫', label: '学校管理', path: '/schools', roles: [] },
  { icon: '📜', label: '政策法规', path: '/policies', roles: [] },
  { icon: '🌾', label: '乡村工作', path: '/rural-works', roles: [] },
  { icon: '📊', label: '统计分析', path: '/data-analysis', roles: [] },
  { icon: '🗺️', label: '地图可视化', path: '/data-analysis/map', roles: [] },
  {
    icon: '🎯',
    label: '考核评估',
    path: '/data-analysis/assessment',
    roles: [],
  },
  { icon: '📅', label: '工作日历', path: '/work-calendar', roles: [] },
]

// 管理员专属导航项
const adminNavItems: NavItem[] = [
  {
    icon: '💰',
    label: '经费管理',
    path: '/funds',
    roles: ['admin', 'super_admin', 'manager'],
  },
  {
    icon: '📋',
    label: '审批管理',
    path: '/approval/pending',
    roles: ['admin', 'super_admin', 'approval_leader', 'manager'],
  },
  {
    icon: '📈',
    label: '数据录入',
    path: '/data-entry/comprehensive',
    roles: [],
  },
  {
    icon: '💾',
    label: '数据备份',
    path: '/data-management/backup',
    roles: ['admin', 'super_admin'],
    requiresAdmin: true,
  },
  {
    icon: '📄',
    label: '报表导出',
    path: '/report-export',
    roles: ['admin', 'super_admin', 'manager'],
  },
  {
    icon: '📥',
    label: '数据导入',
    path: '/data-import/batch',
    roles: ['admin', 'super_admin', 'manager'],
  },
  {
    icon: '📩',
    label: '接收数据包',
    path: '/data-package/receive',
    roles: ['admin', 'super_admin', 'manager'],
  },
  {
    icon: '🔗',
    label: '配置包管理',
    path: '/system/config-package',
    roles: ['admin', 'super_admin'],
  },
  {
    icon: '🔧',
    label: '系统监控',
    path: '/system/monitoring',
    roles: ['admin', 'super_admin'],
    requiresAdmin: true,
  },
]

// 普通用户专属导航项
const userNavItems: NavItem[] = [
  { icon: '💰', label: '经费申请', path: '/funds/user', roles: [] },
  { icon: '📝', label: '经费申请', path: '/funds/apply', roles: [] },
  {
    icon: '📈',
    label: '数据录入',
    path: '/data-entry/comprehensive',
    roles: [],
  },
  { icon: '📤', label: '数据上报', path: '/data-package/report', roles: [] },
  {
    icon: '📝',
    label: '我的申请',
    path: '/approval/my-applications',
    roles: [],
  },
]

/** 检查用户是否有权限访问导航项 */
function hasNavPermission(item: NavItem): boolean {
  // 不需要特定角色
  if (!item.roles || item.roles.length === 0) return true
  // 需要管理员权限
  if (item.requiresAdmin && !isAdminRole.value) return false
  // 检查角色匹配
  return item.roles.includes(userRole.value)
}

/** 导航到指定路径，带权限检查 */
function navigateTo(item: NavItem) {
  if (!hasNavPermission(item)) {
    ElMessage.warning('您没有权限访问此功能')
    return
  }
  pushSafe(item.path)
}

const quickNavItems = computed(() => {
  let items: NavItem[]
  if (isManagerRole.value) {
    items = [...commonNavItems, ...adminNavItems]
  } else {
    items = [...commonNavItems, ...userNavItems]
  }
  // 过滤掉无权限的项
  return items.filter(hasNavPermission)
})

const svgIcons = {
  folder:
    '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="white" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"></path></svg>',
  location:
    '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="white" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>',
  school:
    '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="white" stroke-width="2"><path d="M3 21h18M5 21V7l8-4 8 4v14M8 21v-9a4 4 0 014-4h0a4 4 0 014 4v9"></path></svg>',
  money:
    '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="white" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>',
}

const coreStats = computed(() => {
  const s = dashStats.value
  // 如果没有数据，返回空数组
  if (!s) return []

  return [
    {
      label: '帮扶项目',
      value: s.total_projects || 0,
      icon: svgIcons.folder,
      bgColor: '#40916c',
      extra: `进行中 ${s.active_projects || 0}`,
      path: '/projects',
    },
    {
      label: '帮扶村庄',
      value: s.total_villages || 0,
      icon: svgIcons.location,
      bgColor: '#2196f3',
      extra: `覆盖 ${(s.total_population || 0).toLocaleString()} 人`,
      path: '/villages',
    },
    {
      label: '援建学校',
      value: s.total_schools || 0,
      icon: svgIcons.school,
      bgColor: '#ff9800',
      extra: `帮扶中 ${s.schools_active || 0}`,
      path: '/schools',
    },
    {
      label: '投入资金(万)',
      value: s.total_funds || 0,
      icon: svgIcons.money,
      bgColor: '#e91e63',
      extra: `已拨付 ${s.funds_allocated || 0}万`,
      path: isManagerRole.value ? '/funds' : '/funds/user',
    },
  ]
})

const fundAllocatedPercent = computed(() => {
  const t = dashStats.value?.total_funds || 1
  return Math.round(((dashStats.value?.funds_allocated || 0) / t) * 100)
})
const fundPendingPercent = computed(() => {
  const t = dashStats.value?.total_funds || 1
  return Math.round(((dashStats.value?.funds_pending || 0) / t) * 100)
})
const fundPlannedPercent = computed(() => {
  const t = dashStats.value?.total_funds || 1
  return Math.round(((dashStats.value?.funds_planned || 0) / t) * 100)
})

function formatCurrentDate() {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })
}
const currentDate = ref(formatCurrentDate())
let dateTimer: ReturnType<typeof setInterval> | null = null

const statusMap: Record<string, string> = {
  in_progress: '进行中',
  completed: '已完成',
  planning: '规划中',
  pending: '待审批',
  cancelled: '已取消',
  suspended: '已暂停',
}

const typeMap: Record<string, string> = {
  infrastructure: '基础设施',
  education: '教育帮扶',
  medical: '医疗卫生',
  industry: '产业发展',
  agriculture: '农业发展',
  culture: '文化建设',
  ecology: '生态保护',
  training: '技能培训',
  other: '其他',
}

function translateStatus(status: string) {
  return statusMap[status] || status
}

function translateType(type: string) {
  return typeMap[type] || type
}

function getStatusClass(status: string) {
  if (status === '进行中' || status === 'in_progress') return 'in-progress'
  if (status === '已完成' || status === 'completed') return 'completed'
  if (status === '规划中' || status === 'planning') return 'planning'
  return ''
}

function getProgressColor(val: number) {
  if (val >= 80) return '#40916c'
  if (val >= 50) return '#ff9800'
  return '#f56c6c'
}

function formatBackupSize(bytes: number) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function formatBackupTime(iso: string) {
  if (!iso) return '-'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

async function handleOneKeyBackup() {
  backingUp.value = true
  try {
    await request.post('/system/backup', {
      description: `一键备份 ${new Date().toLocaleString('zh-CN')}`,
    })
    ElMessage.success('备份创建成功！')
  } catch {
    ElMessage.error('备份失败，请稍后重试')
  } finally {
    backingUp.value = false
  }
}

async function loadRestoreBackups() {
  try {
    const res = await request.get('/system/backup', {
      showError: false,
    } as any)
    const d = res.data
    restoreBackups.value = Array.isArray(d) ? d : d?.items || d?.data || []
  } catch {
    restoreBackups.value = []
  }
}

async function restoreFromBackup(filename: string) {
  try {
    await ElMessageBox.confirm(
      `确定从备份 "${filename}" 恢复数据吗？此操作将覆盖当前数据库。`,
      '确认恢复',
      { type: 'warning' }
    )
  } catch {
    return
  }
  restoring.value = true
  try {
    await request.post(`/system/backup/restore/${filename}`)
    ElMessage.success('数据恢复成功！请刷新页面。')
    showRestoreDialog.value = false
  } catch {
    ElMessage.error('恢复失败，请稍后重试')
  } finally {
    restoring.value = false
  }
}

async function handleUploadRestore(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return
  try {
    await ElMessageBox.confirm(
      `确定使用上传的文件 "${file.name}" 恢复数据吗？此操作将覆盖当前数据库。`,
      '确认恢复',
      { type: 'warning' }
    )
  } catch {
    input.value = ''
    return
  }
  restoring.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await request.post('/system/backup/upload-restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('数据恢复成功！请刷新页面。')
    showRestoreDialog.value = false
  } catch {
    ElMessage.error('上传恢复失败')
  } finally {
    restoring.value = false
    input.value = ''
  }
}

// 自动刷新定时器
let refreshTimer: ReturnType<typeof setInterval> | null = null
const REFRESH_INTERVAL = 2 * 60 * 1000 // 2分钟自动刷新

async function refreshDashboard() {
  dashRefreshing.value = true
  try {
    const res = await request.get('/dashboard/stats', {
      params: { refresh: true },
      showError: false,
    } as any)
    // 只有当数据不为空且至少有一个非零值时才设置
    if (res.data && Object.values(res.data).some((v) => typeof v === 'number' && v > 0)) {
      dashStats.value = res.data
    } else {
      dashStats.value = null
    }
  } catch (error) {
    console.error('刷新仪表板数据失败:', error)
    dashStats.value = null
    ElMessage.error('仪表板数据加载失败，请刷新页面重试')
  } finally {
    dashRefreshing.value = false
  }
}

async function loadDashboard() {
  dashLoading.value = true
  const silentConfig = { showError: false } as any
  try {
    const results = await Promise.allSettled([
      request.get('/dashboard/stats', silentConfig),
      request.get('/projects', {
        params: { page: 1, page_size: 5 },
        ...silentConfig,
      }),
      request.get('/dashboard/recent-activities', silentConfig),
      request.get('/messages', silentConfig),
    ])

    // 统计数据（拦截器已自动解包 response => response）
    if (results[0].status === 'fulfilled') {
      const d = results[0].value.data
      // 只有当数据不为空且至少有一个非零值时才设置
      if (d && Object.values(d).some((v) => typeof v === 'number' && v > 0)) {
        dashStats.value = d
      } else {
        dashStats.value = null
      }
    }
    // 项目列表
    if (results[1].status === 'fulfilled') {
      const d = results[1].value.data
      recentProjects.value = (d?.items || (Array.isArray(d) ? d : [])).slice(0, 5)
    }
    // 近期动态
    if (results[2].status === 'fulfilled') {
      const d = results[2].value.data
      recentActivities.value = (d?.items || (Array.isArray(d) ? d : [])).slice(0, 8)
    }
    // 消息
    if (results[3].status === 'fulfilled') {
      const d = results[3].value.data
      messages.value = (d?.items || (Array.isArray(d) ? d : [])).slice(0, 5)
    }
  } finally {
    dashLoading.value = false
  }
}

// 打开恢复弹窗时加载备份列表
watch(showRestoreDialog, (val: boolean) => {
  if (val) loadRestoreBackups()
})

onMounted(() => {
  loadDashboard()
  loadTasks()
  // 定时刷新数据
  refreshTimer = setInterval(() => {
    loadDashboard()
    loadTasks()
  }, REFRESH_INTERVAL)
  // 每分钟更新日期显示（跨日自动刷新）
  dateTimer = setInterval(() => {
    currentDate.value = formatCurrentDate()
  }, 60_000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (dateTimer) {
    clearInterval(dateTimer)
    dateTimer = null
  }
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #1b4332 0%, #40916c 100%);
  border-radius: 12px;
  padding: 28px 32px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 16px rgba(27, 67, 50, 0.25);
}
.welcome-title {
  margin: 0 0 6px 0;
  font-size: 28px;
  font-weight: 700;
  color: #d4af37;
}
.welcome-date {
  margin: 0;
  opacity: 0.85;
  font-size: 13px;
}
.welcome-summary {
  margin: 8px 0 0;
  font-size: 13px;
  opacity: 0.9;
  line-height: 1.5;
}
.welcome-summary strong {
  color: #d4af37;
  font-size: 15px;
}
.quick-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.action-btn {
  border: none;
  padding: 10px 18px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: transform 0.2s;
  white-space: nowrap;
}
.action-btn:hover {
  transform: translateY(-2px);
}
.action-btn.primary {
  background: white;
  color: #1b4332;
  font-weight: 600;
}
.action-btn.secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.4);
}
.action-btn.backup {
  background: linear-gradient(135deg, #d4af37, #f0e68c);
  color: #1b4332;
  font-weight: 600;
}
.action-btn.backup:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}
.action-btn.restore {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.4);
}

/* 恢复弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-dialog {
  background: white;
  border-radius: 12px;
  width: 560px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}
.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1e293b;
}
.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
}
.modal-body {
  padding: 24px;
}
.restore-section {
  margin-bottom: 24px;
}
.restore-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #475569;
}
.backup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}
.backup-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8faf9;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.backup-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.backup-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
}
.backup-meta {
  font-size: 12px;
  color: #94a3b8;
}
.btn-sm {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: none;
}
.restore-btn {
  background: #40916c;
  color: white;
}
.restore-btn:hover {
  background: #1b4332;
}
.restore-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.empty-tip {
  color: #94a3b8;
  font-size: 13px;
  padding: 16px;
  text-align: center;
  background: #f8faf9;
  border-radius: 8px;
}
.upload-area {
  text-align: center;
  padding: 20px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
}
.upload-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #94a3b8;
}
.upload-area .action-btn.secondary {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #d1d5db;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-card {
  background: white;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}
.stat-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14px;
  flex-shrink: 0;
}
.stat-content {
  flex: 1;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #1b4332;
  line-height: 1.2;
}
.stat-label {
  color: #64748b;
  font-size: 13px;
  margin-top: 2px;
}
.stat-extra {
  position: absolute;
  top: 16px;
  right: 16px;
}
.stat-extra-text {
  font-size: 12px;
  color: #40916c;
  background: rgba(64, 145, 108, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

/* 快捷导航 */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  padding: 16px 20px;
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 8px;
  border-radius: 8px;
  background: #f8faf9;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.nav-item:hover {
  border-color: #40916c;
  background: rgba(64, 145, 108, 0.06);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
.nav-icon {
  font-size: 24px;
  margin-bottom: 6px;
}
.nav-label {
  font-size: 12px;
  color: #334155;
  text-align: center;
}

/* 主内容 */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}
.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 通用卡片 */
.section-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.section-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-header h3 {
  margin: 0;
  font-size: 15px;
  color: #1e293b;
}
.section-body {
  padding: 16px 20px;
}
.text-btn {
  background: none;
  border: none;
  color: #40916c;
  cursor: pointer;
  font-size: 13px;
}
.text-btn:hover {
  text-decoration: underline;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th {
  text-align: left;
  color: #64748b;
  font-weight: 500;
  font-size: 13px;
  padding: 0 8px 10px 0;
  border-bottom: 1px solid #f1f5f9;
}
.data-table td {
  padding: 12px 8px 12px 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 13px;
  color: #334155;
}
.data-table tr:last-child td {
  border-bottom: none;
}
.project-name {
  cursor: pointer;
  color: #1b4332;
  font-weight: 500;
}
.project-name:hover {
  color: #40916c;
  text-decoration: underline;
}
.type-tag {
  font-size: 12px;
  color: #475569;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}
.status-badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.in-progress {
  background: #e0f2fe;
  color: #0284c7;
}
.status-badge.completed {
  background: #dcfce7;
  color: #16a34a;
}
.status-badge.planning {
  background: #f1f5f9;
  color: #475569;
}
.progress-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-bar-bg {
  flex: 1;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s;
}
.progress-text {
  font-size: 12px;
  color: #64748b;
  min-width: 32px;
  text-align: right;
}

/* 经费概况 */
.fund-summary-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.fund-summary-item {
  text-align: center;
  padding: 12px;
  background: #f8faf9;
  border-radius: 8px;
}
.fund-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}
.fund-value {
  font-size: 22px;
  font-weight: 700;
  color: #1b4332;
}
.fund-unit {
  font-size: 12px;
  font-weight: 400;
  color: #64748b;
}
.text-green {
  color: #40916c;
}
.text-orange {
  color: #e6a23c;
}
.text-blue {
  color: #409eff;
}
.fund-progress-bar {
  height: 12px;
  background: #f1f5f9;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  margin-bottom: 10px;
}
.fund-bar-allocated {
  background: #40916c;
  transition: width 0.5s;
}
.fund-bar-pending {
  background: #e6a23c;
  transition: width 0.5s;
}
.fund-bar-planned {
  background: #409eff;
  transition: width 0.5s;
}
.fund-legend {
  display: flex;
  gap: 16px;
  justify-content: center;
}
.legend-item {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.legend-dot.green {
  background: #40916c;
}
.legend-dot.orange {
  background: #e6a23c;
}
.legend-dot.blue {
  background: #409eff;
}

/* 近期动态 */
.activity-list {
  display: flex;
  flex-direction: column;
}
.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f8fafc;
}
.activity-item:last-child {
  border-bottom: none;
}
.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.dot-project {
  background: #40916c;
}
.dot-fund {
  background: #e6a23c;
}
.dot-import {
  background: #409eff;
}
.dot-school {
  background: #ff9800;
}
.dot-village {
  background: #2196f3;
}
.dot-policy {
  background: #9c27b0;
}
.activity-content {
  flex: 1;
  font-size: 13px;
}
.activity-action {
  color: #334155;
  font-weight: 500;
  margin-right: 6px;
}
.activity-target {
  color: #1b4332;
}
.activity-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}
.activity-user {
  font-size: 12px;
  color: #40916c;
}
.activity-time {
  font-size: 11px;
  color: #94a3b8;
}

/* 动态编辑 */
.activity-add-form {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.activity-form-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.activity-select {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 12px;
  color: #475569;
  outline: none;
  background: white;
  cursor: pointer;
}
.activity-select:focus {
  border-color: #40916c;
}
.activity-input {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 7px 12px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
  min-width: 100px;
}
.activity-input:focus {
  border-color: #40916c;
}
.activity-input::placeholder {
  color: #94a3b8;
}
.activity-input-wide {
  flex: 1;
}
.activity-add-btn {
  background: #40916c;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 7px 14px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}
.activity-add-btn:hover {
  background: #1b4332;
}
.activity-add-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
.activity-edit-form {
  display: flex;
  gap: 6px;
  align-items: center;
  flex: 1;
}
.activity-select-sm {
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 12px;
  color: #475569;
  outline: none;
  background: white;
  cursor: pointer;
}
.activity-input-sm {
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  outline: none;
  transition: border-color 0.2s;
  min-width: 60px;
}
.activity-input-sm:focus {
  border-color: #40916c;
}
.activity-save-btn {
  background: #40916c;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.activity-save-btn:hover {
  background: #1b4332;
}
.activity-save-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
.activity-cancel-btn {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.activity-cancel-btn:hover {
  background: #e2e8f0;
}
.activity-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}
.activity-item:hover .activity-actions {
  opacity: 1;
}
.activity-edit-btn,
.activity-delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  color: #cbd5e1;
}
.activity-edit-btn:hover {
  color: #40916c;
  background: rgba(64, 145, 108, 0.1);
}
.activity-delete-btn:hover {
  color: #ef4444;
  background: #fee2e2;
}
.activity-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 20px 0;
}

/* 待办 */
.task-add-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.task-input {
  flex: 1;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 7px 12px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}
.task-input:focus {
  border-color: #40916c;
}
.task-input::placeholder {
  color: #94a3b8;
}
.task-priority-select {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 12px;
  color: #475569;
  outline: none;
  background: white;
  cursor: pointer;
}
.task-add-btn {
  background: #40916c;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 7px 14px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}
.task-add-btn:hover {
  background: #1b4332;
}
.task-add-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f8fafc;
}
.task-item:last-child {
  border-bottom: none;
}
.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex: 1;
  min-width: 0;
}
.checkbox-wrapper input {
  display: none;
}
.checkmark {
  width: 16px;
  height: 16px;
  border: 2px solid #cbd5e1;
  border-radius: 4px;
  position: relative;
  transition: all 0.2s;
  flex-shrink: 0;
}
.checkbox-wrapper input:checked + .checkmark {
  background: #40916c;
  border-color: #40916c;
}
.checkbox-wrapper input:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}
.task-text {
  font-size: 13px;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-text.done {
  text-decoration: line-through;
  color: #94a3b8;
}
.task-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.task-delete-btn {
  background: none;
  border: none;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 14px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}
.task-delete-btn:hover {
  color: #ef4444;
  background: #fee2e2;
}
.task-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 20px 0;
}
.priority-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}
.priority-tag.high {
  background: #fee2e2;
  color: #ef4444;
}
.priority-tag.medium {
  background: #ffedd5;
  color: #f59e0b;
}
.priority-tag.low {
  background: #f1f5f9;
  color: #64748b;
}
.badge-count {
  background: #f56c6c;
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 消息 */
.message-list {
  display: flex;
  flex-direction: column;
}
.message-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f8fafc;
}
.message-item:last-child {
  border-bottom: none;
}
.message-item.unread {
  background: rgba(64, 145, 108, 0.03);
  margin: 0 -20px;
  padding: 10px 20px;
}
.msg-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}
.msg-content {
  flex: 1;
  min-width: 0;
}
.msg-title {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 2px;
}
.msg-desc {
  font-size: 12px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.msg-time {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

/* 数据概览 */
.data-overview-list {
  display: flex;
  flex-direction: column;
}
.data-overview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f8fafc;
}
.data-overview-item:last-child {
  border-bottom: none;
}
.do-label {
  font-size: 13px;
  color: #64748b;
}
.do-value {
  font-size: 13px;
  font-weight: 600;
  color: #1b4332;
  display: flex;
  align-items: center;
  gap: 8px;
}
.completeness-bar {
  width: 60px;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
  display: inline-block;
}
.completeness-fill {
  height: 100%;
  background: #40916c;
  border-radius: 3px;
  display: block;
}

/* 骨架屏 */
.skeleton-card {
  pointer-events: none;
}
.skeleton-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: #e2e8f0;
  margin-right: 14px;
  flex-shrink: 0;
  animation: shimmer 1.5s infinite;
}
.skeleton-text-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.skeleton-line {
  height: 14px;
  border-radius: 4px;
  background: #e2e8f0;
  animation: shimmer 1.5s infinite;
}
.skeleton-line.wide {
  width: 60%;
}
.skeleton-line.narrow {
  width: 40%;
}
.skeleton-table {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.skeleton-row {
  display: flex;
  gap: 16px;
}
.skeleton-row .skeleton-line.wide {
  flex: 2;
}
.skeleton-row .skeleton-line.narrow {
  flex: 1;
}
@keyframes shimmer {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
  100% {
    opacity: 1;
  }
}

/* 刷新按钮 */
.stat-refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 18px;
  opacity: 0.6;
  transition: opacity 0.2s;
  grid-column: 1 / -1;
  padding: 4px 0;
}
.stat-refresh:hover {
  opacity: 1;
}
.refreshing {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 空状态 */
.empty-state {
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
  padding: 24px 0;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .main-grid {
    grid-template-columns: 1fr;
  }
  .fund-summary-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 768px) {
  .welcome-banner {
    flex-direction: column;
    gap: 16px;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}
.empty-text {
  font-size: 18px;
  font-weight: 500;
  color: #334155;
  margin-bottom: 8px;
}
.empty-hint {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 24px;
}
.empty-state .action-btn {
  margin: 0 auto;
}

/* 自定义布局按钮 */
.action-btn.layout-btn {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.action-btn.layout-btn:hover {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}

/* 布局编辑器面板 */
.layout-editor-panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 16px;
}
.layout-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 15px;
  font-weight: 700;
  color: #1e293b;
}
.layout-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: #94a3b8;
  padding: 2px 6px;
  line-height: 1;
  border-radius: 4px;
}
.layout-close-btn:hover {
  color: #ef4444;
  background: #fef2f2;
}

/* 预设布局 */
.layout-presets {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
}
.presets-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  white-space: nowrap;
}

.layout-editor-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 18px;
  max-height: 360px;
  overflow-y: auto;
}
.layout-editor-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: grab;
  font-size: 13px;
  color: #334155;
  transition:
    background 0.15s,
    opacity 0.15s;
  border: 1px solid transparent;
}
.layout-editor-item:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}
.layout-editor-item.item-disabled {
  opacity: 0.5;
}
.layout-editor-item.item-disabled:hover {
  opacity: 0.75;
}
.layout-editor-item:active {
  cursor: grabbing;
}
.drag-handle {
  color: #cbd5e1;
  font-size: 18px;
  cursor: grab;
  user-select: none;
  letter-spacing: -2px;
}
.item-order {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  min-width: 16px;
  text-align: center;
}
.item-info {
  flex: 1;
  min-width: 0;
}
.item-label {
  display: block;
  font-weight: 500;
  font-size: 14px;
  color: #334155;
}
.item-desc {
  display: block;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.layout-editor-footer {
  padding: 10px 18px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f0f0f0;
}
.layout-status {
  font-size: 12px;
  color: #94a3b8;
}
.layout-reset-btn {
  background: none;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 5px 14px;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}
.layout-reset-btn:hover {
  border-color: #40916c;
  color: #40916c;
  background: #f0fdf4;
}
</style>
