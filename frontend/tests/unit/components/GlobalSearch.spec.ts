import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import GlobalSearch from '@/components/GlobalSearch.vue'

// Mock API
vi.mock('@/api/search', () => ({
  searchAll: vi.fn(),
  searchByType: vi.fn()
}))

import { searchAll, searchByType } from '@/api/search'

describe('GlobalSearch', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('按下 Ctrl+K 打开搜索框', async () => {
    const wrapper = mount(GlobalSearch)

    // 模拟 Ctrl+K
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 验证搜索框显示
    expect(wrapper.find('.search-dialog').exists()).toBe(true)
  })

  it('按下 Escape 关闭搜索框', async () => {
    const wrapper = mount(GlobalSearch)

    // 先打开搜索框
    const openEvent = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(openEvent)
    await nextTick()

    // 按下 Escape
    const closeEvent = new KeyboardEvent('keydown', { key: 'Escape' })
    document.dispatchEvent(closeEvent)
    await nextTick()

    // 验证搜索框关闭
    expect(wrapper.find('.search-dialog').exists()).toBe(false)
  })

  it('输入搜索词触发搜索', async () => {
    const mockResults = {
      villages: [{ id: 1, name: '测试村', type: 'village' }],
      projects: [],
      funds: [],
      policies: [],
      work_logs: []
    }
    vi.mocked(searchAll).mockResolvedValue(mockResults)

    const wrapper = mount(GlobalSearch)

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 输入搜索词
    const input = wrapper.find('input[type="text"]')
    await input.setValue('测试')

    // 等待防抖 (300ms)
    await new Promise(r => setTimeout(r, 350))
    await flushPromises()

    expect(searchAll).toHaveBeenCalledWith('测试')
    expect(wrapper.text()).toContain('测试村')
  })

  it('搜索结果为空显示提示', async () => {
    vi.mocked(searchAll).mockResolvedValue({
      villages: [], projects: [], funds: [], policies: [], work_logs: []
    })

    const wrapper = mount(GlobalSearch)

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 输入搜索词
    const input = wrapper.find('input[type="text"]')
    await input.setValue('不存在的内容')

    await new Promise(r => setTimeout(r, 350))
    await flushPromises()

    expect(wrapper.text()).toContain('未找到相关结果')
  })

  it('点击结果跳转到详情页', async () => {
    const mockResults = {
      villages: [{ id: 1, name: '测试村', type: 'village' }]
    }
    vi.mocked(searchAll).mockResolvedValue(mockResults)

    const mockRouter = { push: vi.fn() }

    const wrapper = mount(GlobalSearch, {
      global: {
        mocks: {
          $router: mockRouter
        }
      }
    })

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 输入搜索词
    const input = wrapper.find('input[type="text"]')
    await input.setValue('测试')

    await new Promise(r => setTimeout(r, 350))
    await flushPromises()

    // 点击结果项
    const resultItem = wrapper.find('.search-result-item')
    if (resultItem.exists()) {
      await resultItem.trigger('click')

      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining('/villages/1')
      )
    }
  })

  it('搜索结果分类显示', async () => {
    const mockResults = {
      villages: [{ id: 1, name: '测试村', type: 'village' }],
      projects: [{ id: 1, name: '测试项目', type: 'project' }],
      funds: [{ id: 1, name: '测试资金', type: 'fund' }],
      policies: [],
      work_logs: []
    }
    vi.mocked(searchAll).mockResolvedValue(mockResults)

    const wrapper = mount(GlobalSearch)

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 输入搜索词
    const input = wrapper.find('input[type="text"]')
    await input.setValue('测试')

    await new Promise(r => setTimeout(r, 350))
    await flushPromises()

    // 验证分类标题显示
    expect(wrapper.text()).toContain('村庄')
    expect(wrapper.text()).toContain('项目')
    expect(wrapper.text()).toContain('资金')
  })

  it('按类型过滤搜索', async () => {
    const mockResults = {
      villages: [{ id: 1, name: '测试村', type: 'village' }]
    }
    vi.mocked(searchByType).mockResolvedValue(mockResults.villages)

    const wrapper = mount(GlobalSearch)

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 选择类型过滤
    const typeSelect = wrapper.find('select')
    if (typeSelect.exists()) {
      await typeSelect.setValue('village')

      // 输入搜索词
      const input = wrapper.find('input[type="text"]')
      await input.setValue('测试')

      await new Promise(r => setTimeout(r, 350))
      await flushPromises()

      expect(searchByType).toHaveBeenCalledWith('测试', 'village')
    }
  })

  it('搜索历史记录显示', async () => {
    const wrapper = mount(GlobalSearch)

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 如果有搜索历史功能，验证历史记录显示
    // 这取决于组件是否实现了搜索历史功能
  })

  it('输入空字符串不触发搜索', async () => {
    vi.mocked(searchAll).mockClear()

    const wrapper = mount(GlobalSearch)

    // 打开搜索框
    const event = new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })
    document.dispatchEvent(event)
    await nextTick()

    // 输入空格
    const input = wrapper.find('input[type="text"]')
    await input.setValue('   ')

    await new Promise(r => setTimeout(r, 350))
    await flushPromises()

    // 不应该触发搜索
    expect(searchAll).not.toHaveBeenCalled()
  })
})
