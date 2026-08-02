/**
 * MobileBottomNav.vue 测试
 * 覆盖：移动/桌面宽度渲染、active 状态（精确/前缀匹配）、点击导航、badge、resize
 */
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import MobileBottomNav from '@/components/layout/MobileBottomNav.vue'

enableAutoUnmount(afterEach)

vi.mock('@element-plus/icons-vue', () => ({
  HomeFilled: { template: '<i />' },
  Grid: { template: '<i />' },
  Money: { template: '<i />' },
  Message: { template: '<i />' },
  User: { template: '<i />' },
}))

const mocks = vi.hoisted(() => ({
  route: { path: '/dashboard' },
  pushSafe: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => mocks.route,
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: (...a: any[]) => mocks.pushSafe(...a) }),
}))

function setWidth(w: number) {
  Object.defineProperty(window, 'innerWidth', {
    value: w,
    configurable: true,
    writable: true,
  })
}

function mountNav() {
  return mount(MobileBottomNav, {
    global: {
      stubs: {
        'el-icon': { template: '<i class="stub-icon"><slot /></i>' },
      },
    },
  })
}

describe('MobileBottomNav.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.route.path = '/dashboard'
  })

  it('桌面宽度（≥768）不渲染导航', () => {
    setWidth(1024)
    const wrapper = mountNav()
    expect(wrapper.find('nav.mobile-nav').exists()).toBe(false)
  })

  it('移动宽度渲染 5 个导航项', () => {
    setWidth(500)
    const wrapper = mountNav()
    expect(wrapper.find('nav.mobile-nav').exists()).toBe(true)
    const btns = wrapper.findAll('button.nav-btn')
    expect(btns).toHaveLength(5)
    expect(btns[0].text()).toContain('首页')
    expect(btns[4].text()).toContain('我的')
  })

  it('当前路由高亮（精确匹配）', () => {
    setWidth(500)
    mocks.route.path = '/dashboard'
    const wrapper = mountNav()
    const btns = wrapper.findAll('button.nav-btn')
    expect(btns[0].classes()).toContain('active')
    expect(btns[1].classes()).not.toContain('active')
  })

  it('当前路由高亮（前缀匹配：子路由）', () => {
    setWidth(500)
    mocks.route.path = '/supported-villages/123'
    const wrapper = mountNav()
    const btns = wrapper.findAll('button.nav-btn')
    expect(btns[1].classes()).toContain('active')
  })

  it('点击导航项调用 pushSafe', async () => {
    setWidth(500)
    const wrapper = mountNav()
    await wrapper.findAll('button.nav-btn')[3].trigger('click')
    expect(mocks.pushSafe).toHaveBeenCalledWith('/message')
  })

  it('窗口尺寸变化时响应（resize 进出移动端）', async () => {
    setWidth(500)
    const wrapper = mountNav()
    expect(wrapper.find('nav.mobile-nav').exists()).toBe(true)

    setWidth(800)
    window.dispatchEvent(new Event('resize'))
    await nextTick()
    expect(wrapper.find('nav.mobile-nav').exists()).toBe(false)

    setWidth(400)
    window.dispatchEvent(new Event('resize'))
    await nextTick()
    expect(wrapper.find('nav.mobile-nav').exists()).toBe(true)
  })

  it('badge 渲染', async () => {
    setWidth(500)
    const wrapper = mountNav()
    // badge 初始为空字符串 → 不渲染
    expect(wrapper.find('.nav-badge').exists()).toBe(false)
    // 注入 badge 后触发 resize 重渲染
    const state = (wrapper.vm as any).$.setupState
    state.navItems[3].badge = '3'
    setWidth(600)
    window.dispatchEvent(new Event('resize'))
    await nextTick()
    expect(wrapper.find('.nav-badge').exists()).toBe(true)
    expect(wrapper.find('.nav-badge').text()).toBe('3')
  })

  it('卸载时移除 resize 监听', async () => {
    setWidth(500)
    const removeSpy = vi.spyOn(window, 'removeEventListener')
    const wrapper = mountNav()
    wrapper.unmount()
    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    removeSpy.mockRestore()
  })
})
