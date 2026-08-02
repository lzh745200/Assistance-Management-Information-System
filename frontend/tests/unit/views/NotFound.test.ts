/**
 * views/NotFound.vue 覆盖率攻坚
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import { afterEach } from 'vitest'

enableAutoUnmount(afterEach)

const { mockPushSafe } = vi.hoisted(() => ({
  mockPushSafe: vi.fn(() => Promise.resolve()),
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ push: mockPushSafe, pushSafe: mockPushSafe }),
  pushSafe: mockPushSafe,
}))

import NotFound from '@/views/NotFound.vue'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('NotFound.vue', () => {
  it('渲染 404 页面', () => {
    const w = mount(NotFound)
    expect(w.find('.not-found').exists()).toBe(true)
    expect(w.text()).toContain('404')
    expect(w.text()).toContain('页面未找到')
  })

  it('返回首页按钮 → pushSafe("/")', async () => {
    const w = mount(NotFound, {
      global: { stubs: { 'el-button': { template: '<button class="el-button-stub"><slot /></button>' } } },
    })
    const btn = w.find('button')
    await btn.trigger('click')
    expect(mockPushSafe).toHaveBeenCalledWith('/')
  })
})
