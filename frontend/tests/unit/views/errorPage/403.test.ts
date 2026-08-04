/**
 * views/errorPage/403.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：返回首页（pushSafe）、返回上一页（router.go(-1)）。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'

enableAutoUnmount(afterEach)

const { mockPushSafe, mockRouterGo } = vi.hoisted(() => ({
  mockPushSafe: vi.fn(() => Promise.resolve()),
  mockRouterGo: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ go: mockRouterGo, push: vi.fn(), resolve: vi.fn() }),
  useRoute: () => ({ params: {}, query: {} }),
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ push: mockPushSafe, pushSafe: mockPushSafe }),
  pushSafe: mockPushSafe,
}))

import Error403 from '@/views/errorPage/403.vue'

beforeEach(() => {
  vi.resetAllMocks()
})

describe('errorPage/403.vue', () => {
  it('渲染 403 页面内容', async () => {
    const w = mount(Error403)
    await flushPromises()
    expect(w.text()).toContain('403')
    expect(w.text()).toContain('权限不足')
    expect(w.find('.error-page').exists()).toBe(true)
  })

  it('返回首页 → pushSafe("/")', async () => {
    const w = mount(Error403, {
      global: {
        stubs: { 'el-button': { template: '<button class="el-button-stub"><slot /></button>' } },
      },
    })
    await flushPromises()
    const btns = w.findAll('.el-button-stub')
    await btns[0].trigger('click')
    expect(mockPushSafe).toHaveBeenCalledWith('/')
  })

  it('返回上一页 → router.go(-1)', async () => {
    const w = mount(Error403, {
      global: {
        stubs: { 'el-button': { template: '<button class="el-button-stub"><slot /></button>' } },
      },
    })
    await flushPromises()
    const btns = w.findAll('.el-button-stub')
    await btns[1].trigger('click')
    expect(mockRouterGo).toHaveBeenCalledWith(-1)
  })
})
