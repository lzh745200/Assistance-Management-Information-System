import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { mount, enableAutoUnmount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'

enableAutoUnmount(afterEach)

const pushSafeMock = vi.hoisted(() => vi.fn())
vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
}))
vi.mock('vue-router', () => ({
  useRouter: () => ({ currentRoute: { value: { path: '/test' } } }),
}))

const stubs = {
  'el-result': {
    name: 'ElResult',
    props: ['icon', 'title', 'subTitle'],
    template:
      '<div class="el-result"><div class="r-title">{{ title }}</div><div class="r-sub">{{ subTitle }}</div><slot name="extra" /></div>',
  },
  'el-button': {
    name: 'ElButton',
    props: ['type', 'loading'],
    emits: ['click'],
    template: '<button class="el-btn" @click="$emit(\'click\')"><slot /></button>',
  },
}

const BoomChild = defineComponent({
  props: {
    msg: { type: String, default: 'boom' },
    plain: { type: Boolean, default: false },
    err: { type: Object, default: null },
  },
  setup(props) {
    if (props.err) throw props.err
    if (props.plain) {
      throw 'plain string error'
    }
    throw new Error(props.msg)
  },
  render: () => h('div'),
})

async function mountBoundary(msg: string, plain = false) {
  const wrapper = mount(ErrorBoundary, {
    slots: { default: h(BoomChild, { msg, plain }) },
    global: { stubs },
  })
  await flushPromises()
  return wrapper
}

function silenceConsoleError() {
  return vi.spyOn(console, 'error').mockImplementation(() => {})
}

describe('common/ErrorBoundary.vue', () => {
  beforeEach(() => {
    pushSafeMock.mockClear()
  })

  it('renders slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      slots: { default: '<p class="ok">content</p>' },
      global: { stubs },
    })
    expect(wrapper.find('.ok').text()).toBe('content')
  })

  it('classifies chunk load error and renders chunk UI', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('Failed to fetch dynamically imported module')
    expect(wrapper.find('.r-title').text()).toBe('页面模块加载失败')
    expect(wrapper.text()).toContain('重新加载')
    expect(wrapper.text()).toContain('刷新页面')
    expect(wrapper.text()).toContain('忽略')
    consoleError.mockRestore()
  })

  it('classifies Importing a module script failed as chunk error', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('Importing a module script failed')
    expect(wrapper.find('.r-title').text()).toBe('页面模块加载失败')
    consoleError.mockRestore()
  })

  it('classifies network error', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('Failed to fetch')
    expect(wrapper.find('.r-title').text()).toBe('网络连接异常')
    consoleError.mockRestore()
  })

  it('classifies ERR_NETWORK variant', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('ERR_NETWORK connection failed')
    expect(wrapper.find('.r-title').text()).toBe('网络连接异常')
    consoleError.mockRestore()
  })

  it('classifies unknown error with message and stack', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('some unknown error')
    expect(wrapper.find('.r-title').text()).toBe('页面发生异常')
    expect(wrapper.text()).toContain('some unknown error')
    expect(wrapper.text()).toContain('查看详情')
    consoleError.mockRestore()
  })

  it('handles non-Error thrown value', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('ignored', true)
    expect(wrapper.find('.r-title').text()).toBe('页面发生异常')
    consoleError.mockRestore()
  })

  it('falls back to default message and empty stack for empty Error', async () => {
    const consoleError = silenceConsoleError()
    const emptyErr = new Error('')
    Object.defineProperty(emptyErr, 'stack', { value: '' })
    const wrapper = mount(ErrorBoundary, {
      slots: { default: h(BoomChild, { err: emptyErr }) },
      global: { stubs },
    })
    await flushPromises()
    expect(wrapper.find('.r-title').text()).toBe('页面发生异常')
    consoleError.mockRestore()
  })

  it('handleRetry clears error and shows slot again', async () => {
    const consoleError = silenceConsoleError()
    vi.useFakeTimers()
    let shouldThrow = true
    const ToggleChild = defineComponent({
      setup() {
        if (shouldThrow) throw new Error('Failed to fetch dynamically imported module')
        return () => h('p', { class: 'recovered' }, 'recovered')
      },
      render: () => h('div'),
    })
    const wrapper = mount(ErrorBoundary, {
      slots: { default: h(ToggleChild) },
      global: { stubs },
    })
    await flushPromises()
    expect(wrapper.find('.error-boundary-fallback').exists()).toBe(true)

    shouldThrow = false
    const retryButton = wrapper.findAll('button.el-btn').find((b) => b.text().includes('重新加载'))
    await retryButton!.trigger('click')
    await flushPromises()
    expect(wrapper.find('.error-boundary-fallback').exists()).toBe(false)
    expect(wrapper.find('.recovered').text()).toBe('recovered')
    vi.advanceTimersByTime(500)
    vi.useRealTimers()
    consoleError.mockRestore()
  })

  it('handleIgnore hides error UI', async () => {
    const consoleError = silenceConsoleError()
    let shouldThrow = true
    const ToggleChild = defineComponent({
      setup() {
        if (shouldThrow) throw new Error('once')
        return () => h('p', { class: 'recovered' }, 'recovered')
      },
      render: () => h('div'),
    })
    const wrapper = mount(ErrorBoundary, {
      slots: { default: h(ToggleChild) },
      global: { stubs },
    })
    await flushPromises()
    expect(wrapper.find('.error-boundary-fallback').exists()).toBe(true)

    shouldThrow = false
    const ignoreButton = wrapper.findAll('button.el-btn').find((b) => b.text().includes('忽略'))
    await ignoreButton!.trigger('click')
    await flushPromises()
    expect(wrapper.find('.error-boundary-fallback').exists()).toBe(false)
    expect(wrapper.find('.recovered').text()).toBe('recovered')
    consoleError.mockRestore()
  })

  it('handleReload calls window.location.reload', async () => {
    const consoleError = silenceConsoleError()
    const reload = vi.fn()
    const originalLocation = window.location
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, reload },
      configurable: true,
      writable: true,
    })
    try {
      const wrapper = await mountBoundary('unknown')
      const reloadButton = wrapper
        .findAll('button.el-btn')
        .find((b) => b.text().includes('刷新页面'))
      await reloadButton!.trigger('click')
      expect(reload).toHaveBeenCalled()
    } finally {
      Object.defineProperty(window, 'location', {
        value: originalLocation,
        configurable: true,
        writable: true,
      })
    }
    consoleError.mockRestore()
  })

  it('handleGoHome calls pushSafe("/")', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('unknown')
    const homeButton = wrapper.findAll('button.el-btn').find((b) => b.text().includes('返回首页'))
    await homeButton!.trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/')
    consoleError.mockRestore()
  })

  it('toggles showDetail to display stack', async () => {
    const consoleError = silenceConsoleError()
    const wrapper = await mountBoundary('unknown')
    const toggleButton = wrapper.findAll('button.el-btn').find((b) => b.text().includes('详情'))
    await toggleButton!.trigger('click')
    expect(wrapper.find('.error-boundary-stack pre').exists()).toBe(true)
    await toggleButton!.trigger('click')
    expect(wrapper.find('.error-boundary-stack').exists()).toBe(false)
    consoleError.mockRestore()
  })
})
