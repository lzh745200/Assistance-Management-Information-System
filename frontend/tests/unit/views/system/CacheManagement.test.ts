/**
 * views/system/CacheManagement.vue 覆盖率攻坚
 * 覆盖：命中率计算、格式大小、刷新、清空缓存全分支
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, ElMessageBox, mockGet, mockPost } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn(), alert: vi.fn() },
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox,
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import CacheManagement from '@/views/system/CacheManagement.vue'

const statsData = {
  item_count: 500,
  hits: 800,
  misses: 200,
  total_requests: 1000,
  max_size: 10000,
  backend_type: 'redis',
  estimated_size_bytes: 1536,
}

async function mountComp() {
  const w = mount(CacheManagement, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-row': { name: 'ElRow', template: '<div class="el-row-stub"><slot /></div>' },
        'el-col': { name: 'ElCol', template: '<div class="el-col-stub"><slot /></div>' },
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot /><slot name="header" /></div>',
        },
        'el-statistic': {
          name: 'ElStatistic',
          template: '<div class="el-statistic-stub"><slot /></div>',
          props: ['title', 'value'],
        },
        'el-button': {
          name: 'ElButton',
          template: '<button class="el-button-stub"><slot /></button>',
        },
        'el-descriptions': { name: 'ElDescriptions', template: '<dl><slot /></dl>' },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          template: '<div class="el-desc-item-stub"><slot /></div>',
        },
      },
    },
  })
  await flushPromises()
  await nextTick()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGet.mockResolvedValue({ data: statsData })
  mockPost.mockResolvedValue({ success: true, message: '缓存已清除' })
  ElMessageBox.confirm.mockResolvedValue('confirm')
})

describe('CacheManagement.vue', () => {
  it('渲染并加载缓存统计', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(mockGet).toHaveBeenCalledWith('/system/cache/stats')
    expect(vm.stats.item_count).toBe(500)
    expect(vm.hitRateNum).toBe(80)
    expect(w.text()).toContain('redis')
    expect(w.text()).toContain('1.5 KB')
  })

  it('命中率：无请求 → 0', async () => {
    mockGet.mockResolvedValue({ data: {} })
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.hitRateNum).toBe(0)
  })

  it('formatSize 各档位', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    expect(vm.formatSize(0)).toBe('0 B')
    expect(vm.formatSize(undefined)).toBe('0 B')
    expect(vm.formatSize(512)).toBe('512 B')
    expect(vm.formatSize(2048)).toBe('2 KB')
    expect(vm.formatSize(5 * 1024 * 1024)).toBe('5 MB')
    expect(vm.formatSize(2 * 1024 * 1024 * 1024)).toBe('2 GB')
  })

  it('refreshData 失败 → 错误提示', async () => {
    mockGet.mockRejectedValue(new Error('load failed'))
    const w = await mountComp()
    expect(ElMessage.error).toHaveBeenCalledWith('加载缓存信息失败')
    expect((w.vm as any).loading).toBe(false)
  })

  it('refreshData：success=false → 不更新统计', async () => {
    mockGet.mockResolvedValue({ success: false })
    const w = await mountComp()
    expect((w.vm as any).stats.item_count).toBe(0)
  })

  it('refreshData：响应为空 → 空对象兜底', async () => {
    mockGet.mockResolvedValue(null)
    const w = await mountComp()
    expect((w.vm as any).stats).toEqual({})
  })

  it('clearAllCache：确认 → 清除成功并刷新', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.clearAllCache()
    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(mockPost).toHaveBeenCalledWith('/system/cache/clear')
    expect(ElMessage.success).toHaveBeenCalledWith('缓存已清除')
    expect(vm.clearing).toBe(false)
  })

  it('clearAllCache：无 message → 默认文案', async () => {
    mockPost.mockResolvedValue({ success: true })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.clearAllCache()
    expect(ElMessage.success).toHaveBeenCalledWith('缓存已清除')
  })

  it('clearAllCache：用户取消 → 无提示', async () => {
    ElMessageBox.confirm.mockRejectedValue('cancel')
    const w = await mountComp()
    const vm = w.vm as any
    await vm.clearAllCache()
    expect(mockPost).not.toHaveBeenCalled()
    expect(ElMessage.error).not.toHaveBeenCalled()
  })

  it('clearAllCache：失败（非 cancel）→ 错误提示', async () => {
    mockPost.mockRejectedValue(new Error('clear failed'))
    const w = await mountComp()
    const vm = w.vm as any
    await vm.clearAllCache()
    expect(ElMessage.error).toHaveBeenCalledWith('清除失败')
  })

  it('模板按钮：刷新 / 清除全部缓存', async () => {
    const w = await mountComp()
    const refreshBtn = w
      .findAll('button')
      .find((b) => b.text().includes('刷新'))
    await refreshBtn!.trigger('click')
    expect(mockGet).toHaveBeenCalled()
    const clearBtn = w
      .findAll('button')
      .find((b) => b.text().includes('清除全部缓存'))
    await clearBtn!.trigger('click')
    expect(mockPost).toHaveBeenCalledWith('/system/cache/clear')
  })
})
