/**
 * views/HomeSafe.vue 覆盖率攻坚
 * 覆盖：欢迎横幅（用户名为空/角色名回退）、仪表板统计加载/空态/骨架、
 * 核心统计卡片、快捷导航（角色/权限两侧）、布局编辑器（预设/开关/拖拽/重置）、
 * 一键备份/恢复（列表/上传/确认取消）、近期动态 CRUD 全分支、
 * 待办事项 CRUD 全分支、自动刷新与日期定时器、卸载清理。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick, ref } from 'vue'

// vi.mock 工厂会被提升到模块顶部注册，直接引用下方 const 会触发 TDZ；
// 所有被工厂引用的对象放入 vi.hoisted 中先行初始化。
const {
  authState,
  ElMessage,
  confirmMock,
  mockGet,
  mockPost,
  mockPut,
  mockDel,
  mockPatch,
  mockApiRequest,
  pushSafeMock,
  startTourMock,
  logError,
  storageGet,
  storageSet,
  storageRemove,
} = vi.hoisted(() => {
  return {
    authState: { user: { id: 1, name: '管理员', role: 'admin' } as any },
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    confirmMock: vi.fn(),
    mockGet: vi.fn(),
    mockPost: vi.fn(),
    mockPut: vi.fn(),
    mockDel: vi.fn(),
    mockPatch: vi.fn(),
    mockApiRequest: vi.fn(),
    pushSafeMock: vi.fn(),
    startTourMock: vi.fn(),
    logError: vi.fn(),
    storageGet: vi.fn(),
    storageSet: vi.fn(),
    storageRemove: vi.fn(),
  }
})

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
  patch: mockPatch,
  apiRequest: mockApiRequest,
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authState,
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
}))

vi.mock('@/composables/useOnboarding', () => ({
  useOnboarding: () => ({ startTour: startTourMock }),
}))

vi.mock('@/utils/logger', () => ({
  logger: { error: logError, warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}))

vi.mock('@/utils/enhancedStorage', () => ({
  enhancedStorage: { get: storageGet, set: storageSet, remove: storageRemove },
  STORAGE_KEYS: { DASHBOARD_LAYOUT: 'dashboard_layout', DASHBOARD_ORDER: 'dashboard_order' },
}))

vi.mock('@/views/dashboard/components/QuickActions.vue', () => ({
  default: {
    name: 'QuickActions',
    template: '<div class="quick-actions-stub" />',
    props: ['isManager', 'isAdmin', 'backingUp'],
    emits: ['backup', 'restore', 'toggle-layout'],
  },
}))

import HomeSafe from '@/views/HomeSafe.vue'

// ─── 样本数据 ───
const fullStats = {
  total_projects: 5,
  active_projects: 2,
  total_villages: 3,
  total_population: 1000,
  total_schools: 4,
  schools_active: 1,
  total_funds: 100,
  funds_allocated: 50,
  funds_pending: 30,
  funds_planned: 20,
  total_households: 200,
  total_students: 300,
  total_teachers: 40,
  data_completeness: 0.856,
  pending_approvals: 7,
}

const sampleProjects = [
  { id: 1, name: '道路硬化', type: 'infrastructure', status: 'in_progress', progress: 90 },
  { id: 2, name: '希望小学', type: 'education', status: 'completed', progress: 60 },
  { id: 3, name: '卫生室', type: 'medical', status: 'planning', progress: 30 },
  { id: 4, name: '茶园', type: 'mystery_type', status: 'pending', progress: 10 },
  { id: 5, name: '文化广场', type: 'culture', status: 'alien_status', progress: 0 },
]

const sampleActivities = [
  { id: 1, type: 'project', action: '新增', target: '道路硬化', user: 'admin', time: '10:00' },
  { id: 2, type: 'fund', action: '更新', target: '经费拨付', user: 'op', time: '11:00' },
]

const sampleTodos = [
  { id: 1, title: '写报告', priority: 'high', completed: false },
  { id: 2, title: '归档材料', priority: 'strange', completed: true },
]

const sampleBackups = [
  { filename: 'a.db', size: 0, created_at: '' },
  { filename: 'b.db', size: 512, created_at: '2024-01-01T10:00:00Z' },
  { filename: 'c.db', size: 2048, created_at: '2024-01-02T10:00:00Z' },
  { filename: 'd.db.gz', size: 5 * 1024 * 1024, created_at: '2024-01-03T10:00:00Z' },
]

/** 默认 apiRequest（loadDashboard 四路并发）实现，可按 url 覆盖 */
function defaultApiImpl(args: any) {
  const url: string = args.url
  if (url === '/dashboard/stats') return Promise.resolve({ data: fullStats })
  if (url === '/projects') return Promise.resolve({ data: { items: sampleProjects, total: 5 } })
  if (url === '/dashboard/recent-activities') {
    return Promise.resolve({ data: { items: sampleActivities } })
  }
  if (url === '/messages') return Promise.resolve({ data: { items: [{ id: 1, title: 'm' }] } })
  return Promise.resolve({ data: {} })
}

/** 默认 get 实现（待办/备份列表/刷新/动态重载） */
function defaultGetImpl(url: string) {
  if (url === '/todos') return Promise.resolve({ data: { items: sampleTodos } })
  if (url === '/system/backup') return Promise.resolve({ data: { items: sampleBackups } })
  if (url === '/dashboard/stats') return Promise.resolve({ data: { total_projects: 9 } })
  if (url === '/dashboard/recent-activities') {
    return Promise.resolve({ data: { items: sampleActivities } })
  }
  return Promise.resolve({ data: {} })
}

function mountComp() {
  // setup.ts 的全局 el-* stub 默认不渲染插槽，需 renderStubDefaultSlot；
  // 本模板仅用 el-button/el-switch/el-icon，全局 stub 已足够。
  return mount(HomeSafe, {
    global: {
      renderStubDefaultSlot: true,
    },
  })
}

/** 打开恢复弹窗并等待备份列表加载完成 */
async function openRestoreDialog(wrapper: any) {
  await wrapper.findComponent({ name: 'QuickActions' }).vm.$emit('restore')
  await nextTick()
  await flushPromises()
}

beforeEach(() => {
  vi.resetAllMocks()
  authState.user = { id: 1, name: '管理员', role: 'admin' }
  mockApiRequest.mockImplementation(defaultApiImpl)
  mockGet.mockImplementation(defaultGetImpl)
  mockPost.mockResolvedValue({ data: {} })
  mockPut.mockResolvedValue({ data: {} })
  mockDel.mockResolvedValue({ data: {} })
  mockPatch.mockResolvedValue({ data: { completed: true } })
  confirmMock.mockResolvedValue(undefined)
  storageGet.mockReturnValue(null)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('挂载与初始化', () => {
  it('onMounted 加载仪表板四路数据 + 待办，渲染统计卡片/项目/动态/待办', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    expect(mockApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({ method: 'GET', url: '/dashboard/stats' })
    )
    expect(mockApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({ method: 'GET', url: '/projects' })
    )
    expect(mockGet).toHaveBeenCalledWith('/todos')
    expect(vm.dashStats.total_projects).toBe(5)
    expect(vm.recentProjects).toHaveLength(5)
    expect(vm.recentActivities).toHaveLength(2)
    expect(vm.messages).toHaveLength(1)
    expect(vm.tasks).toHaveLength(2)
    // mapTaskItem 命中与回退两侧
    expect(vm.tasks[0].priorityText).toBe('紧急')
    expect(vm.tasks[1].priorityText).toBe('普通')
    // 欢迎横幅
    expect(wrapper.text()).toContain('欢迎回来，管理员')
    expect(wrapper.text()).toContain('当前共有')
    // 统计卡片（4 张）
    expect(wrapper.findAll('.stats-grid .stat-card').length).toBe(4)
    expect(wrapper.findAll('.stat-extra').length).toBe(4)
    // “查看全部”按钮（项目进度 / 经费概况）
    const viewAllBtns = wrapper.findAll('.text-btn')
    await viewAllBtns[0].trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/projects')
    await viewAllBtns[1].trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/funds')
    // 待办徽标（1 个未完成）
    expect(wrapper.find('.badge-count').exists()).toBe(true)
    expect(wrapper.find('.badge-count').text()).toBe('1')
    wrapper.unmount()
  })

  it('欢迎横幅：user 为 null 时回退到角色名', async () => {
    authState.user = null
    const wrapper = mountComp()
    await flushPromises()
    expect(wrapper.text()).toContain('欢迎回来，查看者')
    wrapper.unmount()
  })

  it('欢迎横幅：角色名映射未命中时回退“用户”', async () => {
    authState.user = { id: 9, name: '', role: 'alien_role' }
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(wrapper.text()).toContain('欢迎回来，用户')
    expect(vm.userRoleName).toBe('用户')
    wrapper.unmount()
  })

  it('本地存储存在布局与排序时按保存值初始化（含未知卡片过滤与新卡片追加）', async () => {
    storageGet.mockImplementation((key: string) => {
      if (key === 'dashboard_layout') return { stats: false }
      if (key === 'dashboard_order') return ['funds', 'stats', 'unknown_card']
      return null
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.cardVisibility.stats).toBe(false)
    // 排序以保存值为准，unknown_card 被过滤，缺失卡片追加到尾部
    expect(vm.orderedCards[0].key).toBe('funds')
    expect(vm.orderedCards[1].key).toBe('stats')
    expect(vm.orderedCards).toHaveLength(7)
    expect(vm.orderedCards.map((c: any) => c.key)).not.toContain('unknown_card')
    wrapper.unmount()
  })
})

describe('仪表板加载分支', () => {
  it('加载中渲染骨架（统计骨架 + 项目骨架行）', async () => {
    mockApiRequest.mockReturnValue(new Promise(() => {}))
    mockGet.mockReturnValue(new Promise(() => {}))
    const wrapper = mountComp()
    await nextTick()
    const vm = wrapper.vm as any
    expect(vm.dashLoading).toBe(true)
    expect(wrapper.findAll('.skeleton-card').length).toBe(4)
    expect(wrapper.find('.skeleton-table').exists()).toBe(true)
    wrapper.unmount()
  })

  it('四路全部 reject：各 fulfilled 分支不进入，展示各空态', async () => {
    mockApiRequest.mockRejectedValue(new Error('boom'))
    mockGet.mockRejectedValue(new Error('boom'))
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.dashLoading).toBe(false)
    expect(vm.dashStats).toBeNull()
    expect(vm.recentProjects).toEqual([])
    expect(vm.recentActivities).toEqual([])
    expect(vm.tasks).toEqual([])
    // 空态文案
    expect(wrapper.text()).toContain('暂无统计数据')
    expect(wrapper.text()).toContain('暂无项目数据')
    expect(wrapper.text()).toContain('暂无近期动态')
    expect(wrapper.text()).toContain('暂无待办事项')
    expect(logError).toHaveBeenCalled()
    // 空态“创建第一个项目”按钮
    const createBtn = wrapper.find('.empty-state .action-btn')
    expect(createBtn.exists()).toBe(true)
    await createBtn.trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/projects')
    wrapper.unmount()
  })

  it('stats 为空对象 / projects 与 activities 为裸数组 / messages 无 items 的回退路径', async () => {
    mockApiRequest.mockImplementation((args: any) => {
      const url: string = args.url
      if (url === '/dashboard/stats') return Promise.resolve({ data: {} })
      if (url === '/projects') return Promise.resolve({ data: [] })
      if (url === '/dashboard/recent-activities') return Promise.resolve({ data: [] })
      if (url === '/messages') return Promise.resolve({ data: { weird: 1 } })
      return Promise.resolve({ data: {} })
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.dashStats).toBeNull()
    expect(vm.recentProjects).toEqual([])
    expect(vm.recentActivities).toEqual([])
    expect(vm.messages).toEqual([])
    expect(wrapper.text()).toContain('暂无统计数据')
    wrapper.unmount()
  })

  it('projects/activities 普通对象回退空数组，messages 裸数组直取', async () => {
    mockApiRequest.mockImplementation((args: any) => {
      const url: string = args.url
      if (url === '/dashboard/stats') return Promise.resolve({ data: fullStats })
      if (url === '/projects') return Promise.resolve({ data: { no: 1 } })
      if (url === '/dashboard/recent-activities') return Promise.resolve({ data: { no: 1 } })
      if (url === '/messages') return Promise.resolve({ data: [{ id: 2, title: 'x' }] })
      return Promise.resolve({ data: {} })
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.recentProjects).toEqual([])
    expect(vm.recentActivities).toEqual([])
    expect(vm.messages).toHaveLength(1)
    wrapper.unmount()
  })
})

describe('统计卡片与刷新', () => {
  it('点击统计卡片跳转路径；点击刷新按钮走成功路径', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const cards = wrapper.findAll('.stats-grid .stat-card')
    expect(cards.length).toBe(4)
    await cards[0].trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/projects')
    await cards[1].trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/villages')
    // 刷新（res.data 含正数 → 更新）
    await wrapper.find('.stat-refresh').trigger('click')
    await flushPromises()
    const vm = wrapper.vm as any
    expect(mockGet).toHaveBeenCalledWith('/dashboard/stats')
    expect(vm.dashStats.total_projects).toBe(9)
    expect(vm.dashRefreshing).toBe(false)
    wrapper.unmount()
  })

  it('刷新返回全零数据 → 置空；接口失败 → 错误提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 全零/非数字 → some() false → dashStats = null
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/stats') return Promise.resolve({ data: { label: 'x', zero: 0 } })
      return defaultGetImpl(url)
    })
    await wrapper.find('.stat-refresh').trigger('click')
    await flushPromises()
    expect(vm.dashStats).toBeNull()
    // 恢复统计后走 catch 分支
    vm.dashStats = { ...fullStats }
    await nextTick()
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/stats') return Promise.reject(new Error('net'))
      return defaultGetImpl(url)
    })
    await wrapper.find('.stat-refresh').trigger('click')
    await flushPromises()
    expect(vm.dashStats).toBeNull()
    expect(ElMessage.error).toHaveBeenCalledWith('仪表板数据加载失败，请刷新页面重试')
    wrapper.unmount()
  })

  it('stat.extra 为空时渲染 v-if 假分支（不显示额外角标）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    // 真分支：4 张卡片均有角标
    expect(wrapper.findAll('.stat-extra').length).toBe(4)
    // coreStats 计算属性的 extra 恒为非空字符串，模板 v-if 假分支无法经 dashStats 触达；
    // 直接替换组件内部 setupState 中的 coreStats 绑定，注入无 extra 的卡片
    const vm = wrapper.vm as any
    vm.$.setupState.coreStats = ref([
      { label: '无角标卡', value: 1, icon: '', bgColor: '#000', extra: '', path: '/x' },
    ])
    // 触发一次重渲染使新绑定生效
    vm.dashStats = { ...fullStats, total_projects: 6 }
    await nextTick()
    expect(wrapper.findAll('.stat-extra').length).toBe(0)
    expect(wrapper.text()).toContain('无角标卡')
    wrapper.unmount()
  })

  it('经费进度条百分比计算（total_funds 真/假两侧）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.fundAllocatedPercent).toBe(50)
    expect(vm.fundPendingPercent).toBe(30)
    expect(vm.fundPlannedPercent).toBe(20)
    vm.dashStats = { total_villages: 2 }
    await nextTick()
    expect(vm.fundAllocatedPercent).toBe(0)
    expect(vm.fundPendingPercent).toBe(0)
    expect(vm.fundPlannedPercent).toBe(0)
    // total_projects 缺省时 coreStats 走 || 0 回退
    expect(vm.coreStats[0].value).toBe(0)
    wrapper.unmount()
  })

  it('普通角色经费卡片跳转到 /funds/user', async () => {
    authState.user = { id: 2, name: '访客', role: 'alien_role' }
    const wrapper = mountComp()
    await flushPromises()
    const cards = wrapper.findAll('.stats-grid .stat-card')
    expect(cards.length).toBe(4)
    await cards[3].trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/funds/user')
    wrapper.unmount()
  })
})

describe('快捷导航', () => {
  it('管理员渲染 common+admin 导航项，点击有权限项跳转', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const labels = wrapper.findAll('.nav-item .nav-label').map((n) => n.text())
    expect(labels).toContain('帮扶项目')
    expect(labels).toContain('经费管理')
    expect(labels).toContain('数据备份')
    expect(labels).not.toContain('经费申请')
    const target = wrapper
      .findAll('.nav-item')
      .find((n) => n.find('.nav-label').text() === '数据备份')
    await target!.trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/data-management/backup')
    wrapper.unmount()
  })

  it('非管理角色渲染 common+user 导航项', async () => {
    authState.user = { id: 2, name: '访客', role: 'alien_role' }
    const wrapper = mountComp()
    await flushPromises()
    const labels = wrapper.findAll('.nav-item .nav-label').map((n) => n.text())
    expect(labels).toContain('经费申请')
    expect(labels).toContain('我的申请')
    expect(labels).not.toContain('经费管理')
    wrapper.unmount()
  })

  it('navigateTo 权限检查各分支', async () => {
    authState.user = { id: 2, name: '访客', role: 'alien_role' }
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // requiresAdmin 且非管理员 → 警告
    vm.navigateTo({ icon: null, label: 'x', path: '/x1', roles: ['admin'], requiresAdmin: true })
    expect(ElMessage.warning).toHaveBeenCalledWith('您没有权限访问此功能')
    // roles 非空且不包含当前角色 → 警告
    vm.navigateTo({ icon: null, label: 'y', path: '/x2', roles: ['admin'] })
    expect(ElMessage.warning).toHaveBeenCalledTimes(2)
    // roles 空数组 → 放行
    vm.navigateTo({ icon: null, label: 'z', path: '/ok1', roles: [] })
    expect(pushSafeMock).toHaveBeenCalledWith('/ok1')
    // roles 缺省 → 放行
    vm.navigateTo({ icon: null, label: 'w', path: '/ok2' })
    expect(pushSafeMock).toHaveBeenCalledWith('/ok2')
    wrapper.unmount()
  })
})

describe('布局编辑器', () => {
  it('toggle-layout 打开面板，关闭按钮收起', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const qa = wrapper.findComponent({ name: 'QuickActions' })
    await qa.vm.$emit('toggle-layout')
    await nextTick()
    expect(vm.showLayoutEditor).toBe(true)
    expect(wrapper.find('.layout-editor-panel').exists()).toBe(true)
    await wrapper.find('.layout-close-btn').trigger('click')
    await nextTick()
    expect(vm.showLayoutEditor).toBe(false)
    wrapper.unmount()
  })

  it('四个预设按钮分别应用布局', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await wrapper.findComponent({ name: 'QuickActions' }).vm.$emit('toggle-layout')
    await nextTick()
    const findPreset = (text: string) => {
      const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes(text))
      expect(btn, text).toBeTruthy()
      return btn!
    }
    await findPreset('全部显示').trigger('click')
    expect(vm.currentPreset).toBe('all')
    expect(Object.values(vm.cardVisibility).every(Boolean)).toBe(true)
    await findPreset('管理员视角').trigger('click')
    expect(vm.currentPreset).toBe('manager')
    expect(vm.cardVisibility.todos).toBe(true)
    await findPreset('操作员视角').trigger('click')
    expect(vm.currentPreset).toBe('operator')
    expect(vm.cardVisibility.dataOverview).toBe(false)
    expect(vm.cardVisibility.todos).toBe(false)
    await findPreset('简约模式').trigger('click')
    expect(vm.currentPreset).toBe('minimal')
    expect(vm.cardVisibility.stats).toBe(true)
    expect(vm.cardVisibility.funds).toBe(false)
    // watch 持久化布局
    await nextTick()
    expect(storageSet).toHaveBeenCalledWith('dashboard_layout', expect.any(Object))
    wrapper.unmount()
  })

  it('卡片开关 change 事件切换可见性', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await wrapper.findComponent({ name: 'QuickActions' }).vm.$emit('toggle-layout')
    await nextTick()
    const switches = wrapper.findAllComponents({ name: 'ElSwitch' })
    expect(switches.length).toBe(7)
    await switches[0].vm.$emit('change', false)
    expect(vm.cardVisibility.stats).toBe(false)
    await switches[0].vm.$emit('change', true)
    expect(vm.cardVisibility.stats).toBe(true)
    wrapper.unmount()
  })

  it('拖拽排序全流程：未开始时 dragover 无效、同 index 无效、移动+落库+结束', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await wrapper.findComponent({ name: 'QuickActions' }).vm.$emit('toggle-layout')
    await nextTick()
    const items = wrapper.findAll('.layout-editor-item')
    expect(items.length).toBe(7)
    const keys = () => vm.orderedCards.map((c: any) => c.key)
    const before = keys()
    // dragIndex = -1 → onDragOver 直接返回
    await items[1].trigger('dragover')
    expect(keys()).toEqual(before)
    // 开始拖拽第 0 项
    await items[0].trigger('dragstart')
    // 同 index → 返回
    await items[0].trigger('dragover')
    expect(keys()).toEqual(before)
    // 移动到 index 2
    await items[2].trigger('dragover')
    expect(keys()[2]).toBe(before[0])
    // drop 持久化
    await items[2].trigger('drop')
    expect(storageSet).toHaveBeenCalledWith('dashboard_order', keys())
    // dragend 复位
    await items[0].trigger('dragend')
    wrapper.unmount()
  })

  it('恢复默认布局', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await wrapper.findComponent({ name: 'QuickActions' }).vm.$emit('toggle-layout')
    await nextTick()
    // 先打乱
    const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes('简约模式'))
    await btn!.trigger('click')
    expect(vm.cardVisibility.funds).toBe(false)
    await wrapper.find('.layout-reset-btn').trigger('click')
    expect(Object.values(vm.cardVisibility).every(Boolean)).toBe(true)
    expect(vm.currentPreset).toBe('default')
    expect(vm.orderedCards[0].key).toBe('stats')
    expect(storageRemove).toHaveBeenCalledWith('dashboard_order')
    wrapper.unmount()
  })
})

describe('一键备份', () => {
  it('备份成功与失败两条路径', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const qa = wrapper.findComponent({ name: 'QuickActions' })
    mockPost.mockResolvedValueOnce({ data: { ok: true } })
    await qa.vm.$emit('backup')
    await flushPromises()
    expect(mockPost).toHaveBeenCalledWith('/system/backup', {
      description: expect.stringContaining('一键备份'),
    })
    expect(ElMessage.success).toHaveBeenCalledWith('备份创建成功！')
    expect(vm.backingUp).toBe(false)
    mockPost.mockRejectedValueOnce(new Error('boom'))
    await qa.vm.$emit('backup')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('备份失败，请稍后重试')
    expect(vm.backingUp).toBe(false)
    wrapper.unmount()
  })
})

describe('恢复数据弹窗', () => {
  it('打开弹窗加载备份列表，四种大小格式化 + 时间空值回退', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await openRestoreDialog(wrapper)
    expect(mockGet).toHaveBeenCalledWith('/system/backup')
    const text = wrapper.text()
    expect(text).toContain('0 B')
    expect(text).toContain('512 B')
    expect(text).toContain('2.0 KB')
    expect(text).toContain('5.00 MB')
    expect(text).toContain('-')
    expect(wrapper.findAll('.backup-item').length).toBe(4)
    wrapper.unmount()
  })

  it('备份列表空态（接口失败）与弹窗遮罩/关闭按钮', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/system/backup') return Promise.reject(new Error('boom'))
      return defaultGetImpl(url)
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await openRestoreDialog(wrapper)
    expect(wrapper.text()).toContain('暂无备份文件')
    // 遮罩 click.self 关闭
    await wrapper.find('.modal-overlay').trigger('click')
    await nextTick()
    expect(vm.showRestoreDialog).toBe(false)
    // 重新打开（失败 → 空列表），再用关闭按钮关闭
    await openRestoreDialog(wrapper)
    await wrapper.find('.modal-close').trigger('click')
    await nextTick()
    expect(vm.showRestoreDialog).toBe(false)
    wrapper.unmount()
  })

  it('备份列表数据形态回退：数组 / data 字段 / 空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 数组形态
    mockGet.mockImplementation((url: string) => {
      if (url === '/system/backup') return Promise.resolve({ data: sampleBackups })
      return defaultGetImpl(url)
    })
    await openRestoreDialog(wrapper)
    expect(vm.restoreBackups).toHaveLength(4)
    await wrapper.find('.modal-close').trigger('click')
    await nextTick()
    // d.data 形态
    mockGet.mockImplementation((url: string) => {
      if (url === '/system/backup') return Promise.resolve({ data: { data: sampleBackups } })
      return defaultGetImpl(url)
    })
    await openRestoreDialog(wrapper)
    expect(vm.restoreBackups).toHaveLength(4)
    await wrapper.find('.modal-close').trigger('click')
    await nextTick()
    // 空形态
    mockGet.mockImplementation((url: string) => {
      if (url === '/system/backup') return Promise.resolve({ data: {} })
      return defaultGetImpl(url)
    })
    await openRestoreDialog(wrapper)
    expect(vm.restoreBackups).toEqual([])
    expect(wrapper.text()).toContain('暂无备份文件')
    wrapper.unmount()
  })

  it('从备份恢复：确认成功 / 取消 / 接口失败', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 成功
    mockPost.mockResolvedValueOnce({ data: {} })
    await openRestoreDialog(wrapper)
    await wrapper.findAll('.restore-btn')[0].trigger('click')
    await flushPromises()
    expect(mockPost).toHaveBeenCalledWith('/system/backup/restore', { filename: 'a.db' })
    expect(ElMessage.success).toHaveBeenCalledWith('数据恢复成功！请刷新页面。')
    expect(vm.showRestoreDialog).toBe(false)
    expect(vm.restoring).toBe(false)
    // 取消确认 → 不调接口
    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    await openRestoreDialog(wrapper)
    const beforeCalls = mockPost.mock.calls.length
    await wrapper.findAll('.restore-btn')[0].trigger('click')
    await flushPromises()
    expect(mockPost.mock.calls.length).toBe(beforeCalls)
    // 接口失败
    await wrapper.find('.modal-close').trigger('click')
    await nextTick()
    mockPost.mockRejectedValueOnce(new Error('boom'))
    await openRestoreDialog(wrapper)
    await wrapper.findAll('.restore-btn')[0].trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('恢复失败，请稍后重试')
    expect(vm.restoring).toBe(false)
    wrapper.unmount()
  })

  it('formatBackupTime 日期格式化异常时回退原始字符串', async () => {
    const wrapper = mountComp()
    await flushPromises()
    // 强制 toLocaleString 抛错，覆盖 catch 分支
    const spy = vi
      .spyOn(Date.prototype, 'toLocaleString')
      .mockImplementation(() => {
        throw new Error('icu error')
      })
    await openRestoreDialog(wrapper)
    // catch 后回退展示原始 ISO 字符串
    expect(wrapper.text()).toContain('2024-01-01T10:00:00Z')
    spy.mockRestore()
    wrapper.unmount()
  })

  it('restoring 为 true 时按钮显示“恢复中...”', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await openRestoreDialog(wrapper)
    vm.restoring = true
    await nextTick()
    expect(wrapper.findAll('.restore-btn')[0].text()).toContain('恢复中')
    vm.restoring = false
    await nextTick()
    expect(wrapper.findAll('.restore-btn')[0].text()).toContain('恢复')
    wrapper.unmount()
  })

  it('上传按钮点击触发文件选择（ref 存在与缺失两侧）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await openRestoreDialog(wrapper)
    const uploadBtn = wrapper.find('.upload-area .action-btn')
    expect(uploadBtn.exists()).toBe(true)
    // ref 存在 → 调用 input.click()
    const fileInput = wrapper.find('input[type="file"]')
    const clickSpy = vi.spyOn(fileInput.element as HTMLInputElement, 'click')
    await uploadBtn.trigger('click')
    expect(clickSpy).toHaveBeenCalled()
    // ref 缺失 → 可选链短路（不应抛错）
    delete (wrapper.vm.$refs as any).restoreFileInput
    await uploadBtn.trigger('click')
    wrapper.unmount()
  })

  it('上传文件恢复：成功 / 取消确认 / 接口失败 / 无文件', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await openRestoreDialog(wrapper)
    const file = new File(['db'], 'backup.db', { type: 'application/octet-stream' })
    const getInput = () => wrapper.find('input[type="file"]')
    const setFiles = (files: File[]) => {
      Object.defineProperty(getInput().element, 'files', { value: files, configurable: true })
    }
    // 成功
    mockPost.mockResolvedValueOnce({ data: {} })
    setFiles([file])
    await getInput().trigger('change')
    await flushPromises()
    expect(mockPost).toHaveBeenCalledWith(
      '/system/backup/upload-restore',
      expect.any(FormData),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
    )
    expect(ElMessage.success).toHaveBeenCalledWith('数据恢复成功！请刷新页面。')
    // 取消确认
    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    await openRestoreDialog(wrapper)
    const beforeCalls = mockPost.mock.calls.length
    setFiles([file])
    await getInput().trigger('change')
    await flushPromises()
    expect(mockPost.mock.calls.length).toBe(beforeCalls)
    // 接口失败
    mockPost.mockRejectedValueOnce(new Error('boom'))
    await openRestoreDialog(wrapper)
    setFiles([file])
    await getInput().trigger('change')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('上传恢复失败')
    // 无文件 → 直接返回
    const calls2 = mockPost.mock.calls.length
    setFiles([])
    await getInput().trigger('change')
    await flushPromises()
    expect(mockPost.mock.calls.length).toBe(calls2)
    wrapper.unmount()
  })
})

describe('近期动态 CRUD', () => {
  it('添加动态：成功带 id / 无 id 走重载 / 失败提示 / 空输入拦截', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 打开表单（再次点击可收起）
    const toggleBtn = () =>
      wrapper.findAll('button').find((b) => b.text().includes('添加动态') || b.text() === '取消')!
    await toggleBtn().trigger('click')
    await nextTick()
    expect(vm.showActivityForm).toBe(true)
    // 空输入 → 拦截（按钮 disabled，直接调用方法覆盖早退分支）
    const beforeCalls = mockPost.mock.calls.length
    await wrapper.find('.activity-add-btn').trigger('click')
    await vm.addActivity()
    expect(mockPost.mock.calls.length).toBe(beforeCalls)
    // 填写并提交（created 带 id → 本地 unshift）
    await wrapper.find('select.activity-select').setValue('fund')
    const inputs = wrapper.findAll('.activity-add-form .activity-input')
    await inputs[0].setValue(' 新增 ')
    await inputs[1].setValue(' XX项目 ')
    mockPost.mockResolvedValueOnce({
      data: { id: 9, type: 'fund', action: '新增', target: 'XX项目', user: 'admin', time: '12:00' },
    })
    await wrapper.find('.activity-add-btn').trigger('click')
    await flushPromises()
    expect(mockPost).toHaveBeenCalledWith('/dashboard/recent-activities', {
      type: 'fund',
      action: '新增',
      target: 'XX项目',
    })
    expect(vm.recentActivities[0].id).toBe(9)
    expect(vm.showActivityForm).toBe(false)
    expect(vm.newActivity).toEqual({ type: 'project', action: '', target: '' })
    // created 无 id → reloadActivities
    await toggleBtn().trigger('click')
    await nextTick()
    const inputs2 = wrapper.findAll('.activity-add-form .activity-input')
    await inputs2[0].setValue('更新')
    await inputs2[1].setValue('YY项目')
    mockPost.mockResolvedValueOnce({ data: null })
    await wrapper.find('.activity-add-btn').trigger('click')
    await flushPromises()
    expect(mockGet).toHaveBeenCalledWith('/dashboard/recent-activities')
    // 接口失败 → 错误提示（带 detail）
    await toggleBtn().trigger('click')
    await nextTick()
    const inputs3 = wrapper.findAll('.activity-add-form .activity-input')
    await inputs3[0].setValue('更新')
    await inputs3[1].setValue('ZZ项目')
    mockPost.mockRejectedValueOnce({ response: { data: { detail: '冲突' } } })
    await wrapper.find('.activity-add-btn').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('添加动态失败: 冲突')
    // 接口失败：普通 Error（无 detail，回退 e.message）——失败路径表单保持打开
    mockPost.mockRejectedValueOnce(new Error('网络断开'))
    await wrapper.find('.activity-add-btn').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('添加动态失败: 网络断开')
    wrapper.unmount()
  })

  it('编辑动态：保存成功 / 空输入拦截 / 接口失败本地更新 / 记录不存在两侧', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 进入编辑
    await wrapper.findAll('.activity-edit-btn')[0].trigger('click')
    await nextTick()
    expect(vm.editingActivityId).toBe(1)
    // 空输入 → 拦截（按钮 disabled，直接调用方法覆盖早退分支）
    const editInputs = wrapper.findAll('.activity-edit-form .activity-input-sm')
    await editInputs[0].setValue(' ')
    vm.editingActivity = { type: 'project', action: ' ', target: '' }
    const beforeCalls = mockPut.mock.calls.length
    await vm.saveActivity(1)
    expect(mockPut.mock.calls.length).toBe(beforeCalls)
    // 正常保存
    await wrapper.find('select.activity-select-sm').setValue('village')
    await editInputs[0].setValue(' 修改 ')
    await editInputs[1].setValue(' 新目标 ')
    mockPut.mockResolvedValueOnce({ data: { user: 'admin2' } })
    await wrapper.find('.activity-save-btn').trigger('click')
    await flushPromises()
    expect(mockPut).toHaveBeenCalledWith('/dashboard/recent-activities/1', {
      type: 'village',
      action: '修改',
      target: '新目标',
    })
    expect(vm.editingActivityId).toBeNull()
    expect(vm.recentActivities[0].action).toBe('修改')
    expect(vm.recentActivities[0].user).toBe('admin2')
    // 接口失败 → 本地更新
    await wrapper.findAll('.activity-edit-btn')[1].trigger('click')
    await nextTick()
    const editInputs2 = wrapper.findAll('.activity-edit-form .activity-input-sm')
    await editInputs2[0].setValue('本地改')
    await editInputs2[1].setValue('本地目标')
    mockPut.mockRejectedValueOnce(new Error('boom'))
    await wrapper.find('.activity-save-btn').trigger('click')
    await flushPromises()
    expect(logError).toHaveBeenCalled()
    expect(vm.recentActivities[1].action).toBe('本地改')
    expect(vm.editingActivityId).toBeNull()
    // 记录不存在（成功路径 idx === -1）
    await wrapper.findAll('.activity-edit-btn')[0].trigger('click')
    await nextTick()
    const editInputs3 = wrapper.findAll('.activity-edit-form .activity-input-sm')
    await editInputs3[0].setValue('x')
    await editInputs3[1].setValue('y')
    vm.recentActivities = []
    mockPut.mockResolvedValueOnce({ data: {} })
    await wrapper.find('.activity-save-btn').trigger('click')
    await flushPromises()
    expect(vm.editingActivityId).toBeNull()
    // 记录不存在（失败路径 idx === -1）
    vm.recentActivities = sampleActivities.map((a) => ({ ...a }))
    await nextTick()
    await wrapper.findAll('.activity-edit-btn')[0].trigger('click')
    await nextTick()
    const editInputs4 = wrapper.findAll('.activity-edit-form .activity-input-sm')
    await editInputs4[0].setValue('x')
    await editInputs4[1].setValue('y')
    vm.recentActivities = []
    mockPut.mockRejectedValueOnce(new Error('boom'))
    await wrapper.find('.activity-save-btn').trigger('click')
    await flushPromises()
    expect(vm.editingActivityId).toBeNull()
    wrapper.unmount()
  })

  it('取消编辑', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await wrapper.findAll('.activity-edit-btn')[0].trigger('click')
    await nextTick()
    expect(vm.editingActivityId).toBe(1)
    await wrapper.find('.activity-cancel-btn').trigger('click')
    expect(vm.editingActivityId).toBeNull()
    expect(vm.editingActivity).toEqual({ type: '', action: '', target: '' })
    wrapper.unmount()
  })

  it('删除动态：确认成功 / 取消 / 接口失败仍本地移除', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 确认删除成功
    mockDel.mockResolvedValueOnce({ data: {} })
    await wrapper.findAll('.activity-delete-btn')[0].trigger('click')
    await flushPromises()
    expect(mockDel).toHaveBeenCalledWith('/dashboard/recent-activities/1')
    expect(vm.recentActivities.map((a: any) => a.id)).toEqual([2])
    // 取消确认
    confirmMock.mockRejectedValueOnce(new Error('cancel'))
    const beforeCalls = mockDel.mock.calls.length
    await wrapper.findAll('.activity-delete-btn')[0].trigger('click')
    await flushPromises()
    expect(mockDel.mock.calls.length).toBe(beforeCalls)
    expect(vm.recentActivities).toHaveLength(1)
    // 接口失败仍本地移除
    mockDel.mockRejectedValueOnce(new Error('boom'))
    await wrapper.findAll('.activity-delete-btn')[0].trigger('click')
    await flushPromises()
    expect(logError).toHaveBeenCalled()
    expect(vm.recentActivities).toHaveLength(0)
    expect(wrapper.text()).toContain('暂无近期动态')
    wrapper.unmount()
  })

  it('reloadActivities 接口失败只记录日志；数据形态回退各分支', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/recent-activities') return Promise.reject(new Error('boom'))
      return defaultGetImpl(url)
    })
    await vm.reloadActivities()
    expect(logError).toHaveBeenCalledWith('加载动态失败')
    // d 为 null → d?.items 短路 + 数组回退 []
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/recent-activities') return Promise.resolve({ data: null })
      return defaultGetImpl(url)
    })
    await vm.reloadActivities()
    expect(vm.recentActivities).toEqual([])
    // d 为裸数组 → Array.isArray 真分支
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/recent-activities') return Promise.resolve({ data: sampleActivities })
      return defaultGetImpl(url)
    })
    await vm.reloadActivities()
    expect(vm.recentActivities).toHaveLength(2)
    // d 为普通对象 → 回退 []
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/recent-activities') return Promise.resolve({ data: { no: 1 } })
      return defaultGetImpl(url)
    })
    await vm.reloadActivities()
    expect(vm.recentActivities).toEqual([])
    wrapper.unmount()
  })
})

describe('待办事项 CRUD', () => {
  it('添加待办：成功带 id / 无 id 走重载 / 失败两种错误形态 / 空标题拦截 / 回车提交', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 空标题 → 拦截（按钮 disabled，直接调用方法覆盖早退分支）
    const beforeCalls = mockPost.mock.calls.length
    await wrapper.find('.task-add-btn').trigger('click')
    await vm.addTask()
    expect(mockPost.mock.calls.length).toBe(beforeCalls)
    // 正常添加（created 带 id）
    await wrapper.find('.task-input').setValue('新待办')
    await wrapper.find('select.task-priority-select').setValue('high')
    mockPost.mockResolvedValueOnce({
      data: { id: 3, title: '新待办', priority: 'high', completed: false },
    })
    await wrapper.find('.task-add-btn').trigger('click')
    await flushPromises()
    expect(mockPost).toHaveBeenCalledWith('/todos', { title: '新待办', priority: 'high' })
    expect(vm.tasks[0].id).toBe(3)
    expect(vm.tasks[0].priorityText).toBe('紧急')
    expect(vm.newTaskTitle).toBe('')
    // created 无 id → loadTasks 重载
    await wrapper.find('.task-input').setValue('第二条')
    mockPost.mockResolvedValueOnce({ data: null })
    await wrapper.find('.task-add-btn').trigger('click')
    await flushPromises()
    expect(mockGet).toHaveBeenCalledWith('/todos')
    // 回车提交
    await wrapper.find('.task-input').setValue('回车待办')
    mockPost.mockResolvedValueOnce({ data: { id: 4, title: '回车待办', priority: 'medium' } })
    await wrapper.find('.task-input').trigger('keyup.enter')
    await flushPromises()
    expect(mockPost).toHaveBeenCalledWith('/todos', { title: '回车待办', priority: 'high' })
    // 失败：带 detail
    await wrapper.find('.task-input').setValue('x')
    mockPost.mockRejectedValueOnce({ response: { data: { detail: '重复' } } })
    await wrapper.find('.task-add-btn').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('添加待办失败: 重复')
    // 失败：普通 Error
    await wrapper.find('.task-input').setValue('y')
    mockPost.mockRejectedValueOnce(new Error('网络断开'))
    await wrapper.find('.task-add-btn').trigger('click')
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('添加待办失败: 网络断开')
    wrapper.unmount()
  })

  it('勾选切换：updated 真值 / updated 空值本地翻转 / 无 data 字段 / 失败 / 未找到任务', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const checkbox = () => wrapper.findAll('.task-item input[type="checkbox"]')[0]
    // updated 真值
    mockPatch.mockResolvedValueOnce({ data: { completed: true } })
    await checkbox().trigger('change')
    await flushPromises()
    expect(mockPatch).toHaveBeenCalledWith('/todos/1/toggle')
    expect(vm.tasks[0].completed).toBe(true)
    // updated 空值（响应整体为 false）→ 本地翻转
    mockPatch.mockResolvedValueOnce(false as any)
    await checkbox().trigger('change')
    await flushPromises()
    expect(vm.tasks[0].completed).toBe(false)
    // 响应无 data 字段 → res.data || res 右侧
    mockPatch.mockResolvedValueOnce({ completed: true })
    await checkbox().trigger('change')
    await flushPromises()
    expect(vm.tasks[0].completed).toBe(true)
    // 失败 → 日志
    mockPatch.mockRejectedValueOnce(new Error('boom'))
    await checkbox().trigger('change')
    await flushPromises()
    expect(logError).toHaveBeenCalled()
    // 未找到任务 → 直接返回
    const beforeCalls = mockPatch.mock.calls.length
    await vm.toggleTask(999)
    expect(mockPatch.mock.calls.length).toBe(beforeCalls)
    wrapper.unmount()
  })

  it('删除待办：成功 / 失败', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    mockDel.mockResolvedValueOnce({ data: {} })
    await wrapper.findAll('.task-delete-btn')[0].trigger('click')
    await flushPromises()
    expect(mockDel).toHaveBeenCalledWith('/todos/1')
    expect(vm.tasks.map((t: any) => t.id)).toEqual([2])
    mockDel.mockRejectedValueOnce(new Error('boom'))
    await wrapper.findAll('.task-delete-btn')[0].trigger('click')
    await flushPromises()
    expect(logError).toHaveBeenCalled()
    expect(vm.tasks).toHaveLength(1)
    wrapper.unmount()
  })

  it('loadTasks 数据形态：裸数组 / 空对象回退 / 全部完成无徽标', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/todos') return Promise.resolve([{ id: 5, title: 'x', priority: 'low', completed: true }])
      return defaultGetImpl(url)
    })
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.tasks).toHaveLength(1)
    expect(vm.pendingTodos).toBe(0)
    expect(wrapper.find('.badge-count').exists()).toBe(false)
    // 空对象 → 空列表
    mockGet.mockImplementation((url: string) => {
      if (url === '/todos') return Promise.resolve({ data: {} })
      return defaultGetImpl(url)
    })
    await vm.loadTasks()
    expect(vm.tasks).toEqual([])
    expect(wrapper.text()).toContain('暂无待办事项')
    wrapper.unmount()
  })
})

describe('项目列表渲染辅助函数', () => {
  it('状态/类型翻译与进度颜色在渲染中覆盖全部分支', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const text = wrapper.text()
    // translateStatus 命中
    expect(text).toContain('进行中')
    expect(text).toContain('已完成')
    expect(text).toContain('规划中')
    expect(text).toContain('待审批')
    // translateStatus 未命中原样返回
    expect(text).toContain('alien_status')
    // translateType 命中与未命中
    expect(text).toContain('基础设施')
    expect(text).toContain('mystery_type')
    // getStatusClass 各分支
    const badges = wrapper.findAll('.status-badge')
    const classes = badges.map((b) => b.classes().join(' '))
    expect(classes.some((c) => c.includes('in-progress'))).toBe(true)
    expect(classes.some((c) => c.includes('completed'))).toBe(true)
    expect(classes.some((c) => c.includes('planning'))).toBe(true)
    // getProgressColor 三档（jsdom 将 hex 归一化为 rgb）
    const fills = wrapper.findAll('.progress-bar-fill')
    const styles = fills.map((f) => f.attributes('style') || '')
    expect(styles.some((s) => s.includes('rgb(64, 145, 108)'))).toBe(true)
    expect(styles.some((s) => s.includes('rgb(255, 152, 0)'))).toBe(true)
    expect(styles.some((s) => s.includes('rgb(245, 108, 108)'))).toBe(true)
    // 项目名点击跳转详情
    await wrapper.findAll('.project-name')[0].trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/projects/1')
    wrapper.unmount()
  })
})

describe('定时器与卸载', () => {
  it('自动刷新与日期定时器回调执行，卸载时清理', async () => {
    vi.useFakeTimers()
    try {
      const wrapper = mountComp()
      await vi.advanceTimersByTimeAsync(0)
      const apiCalls = mockApiRequest.mock.calls.length
      const getCalls = mockGet.mock.calls.length
      // 2 分钟自动刷新
      await vi.advanceTimersByTimeAsync(2 * 60 * 1000)
      expect(mockApiRequest.mock.calls.length).toBeGreaterThan(apiCalls)
      expect(mockGet.mock.calls.length).toBeGreaterThan(getCalls)
      // 1 分钟日期刷新
      await vi.advanceTimersByTimeAsync(60 * 1000)
      // 卸载清理两个定时器
      wrapper.unmount()
      const apiCalls2 = mockApiRequest.mock.calls.length
      await vi.advanceTimersByTimeAsync(2 * 60 * 1000)
      expect(mockApiRequest.mock.calls.length).toBe(apiCalls2)
    } finally {
      vi.useRealTimers()
    }
  })
})
