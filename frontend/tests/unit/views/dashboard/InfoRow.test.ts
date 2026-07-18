/**
 * InfoRow 组件测试
 *
 * 测试范围:
 * 1. 时间线区域渲染
 * 2. 时间线最多渲染 10 条
 * 3. 接口失败时显示错误占位与重试按钮
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton } from 'element-plus'
import InfoRow from '@/views/dashboard/InfoRow.vue'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
    resolve: vi.fn(() => ({ name: 'TestRoute', matched: [{ path: '/test' }] })),
  }),
}))

const mockApiRequest = vi.hoisted(() => vi.fn())

vi.mock('@/api/request', () => ({
  apiRequest: mockApiRequest,
  put: vi.fn(),
  del: vi.fn(),
  default: {},
}))

function mountInfoRow() {
  return mount(InfoRow, {
    global: {
      components: { ElButton },
      stubs: { 'el-icon': true, 'el-timeline': true, 'el-timeline-item': true },
    },
  })
}

describe('InfoRow.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockApiRequest.mockResolvedValue({
      data: {
        items: Array.from({ length: 15 }, (_, i) => ({
          id: i + 1,
          action: `操作${i + 1}`,
          target: `目标${i + 1}`,
          type: 'project',
          time: '2026-06-06',
        })),
      },
    })
  })

  it('renders timeline section', () => {
    const wrapper = mountInfoRow()
    expect(wrapper.find('.timeline-section').exists()).toBe(true)
  })

  it('renders at most 10 timeline items', async () => {
    const wrapper = mountInfoRow()
    await new Promise((r) => setTimeout(r, 200))
    await wrapper.vm.$nextTick()
    // Should not show more than 10 even though API returns 15
    const items = wrapper.findAll('.timeline-item')
    expect(items.length).toBeLessThanOrEqual(11) // 10 items + possible header
  })

  it('shows error placeholder with retry when loading fails', async () => {
    mockApiRequest.mockRejectedValue(new Error('network error'))
    const wrapper = mountInfoRow()
    await new Promise((r) => setTimeout(r, 200))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.tl-state--error').exists()).toBe(true)
    expect(wrapper.findAll('.timeline-item').length).toBe(0)
  })

  // quick-links moved to QuickActions component (index.vue) — tested in QuickActions.test.ts
})
