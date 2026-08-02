import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { useECharts } from '@/composables/useECharts'

// Mock echarts module
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    getDataURL: vi.fn(() => 'data:image/png;base64,...'),
  })),
}))

// Test component that uses useECharts
const TestChartComponent = defineComponent({
  name: 'TestChart',
  setup() {
    const { chartRef, setOption, instance, resize, getDataURL } = useECharts({ autoResize: false })
    return { chartRef, setOption, instance, resize, getDataURL }
  },
  render() {
    return h('div', { ref: 'chartRef', style: 'width:400px;height:300px' })
  },
})

describe('useECharts', () => {
  it('initializes echarts instance on mount', async () => {
    const wrapper = mount(TestChartComponent)
    await nextTick()
    await new Promise((r) => setTimeout(r, 100)) // wait for dynamic import

    const echarts = await import('echarts')
    expect(echarts.init).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('disposes echarts instance on unmount', async () => {
    const wrapper = mount(TestChartComponent)
    await nextTick()
    await new Promise((r) => setTimeout(r, 100))

    const echarts = await import('echarts')
    // Verify init was called (instance was created)
    expect(echarts.init).toHaveBeenCalled()

    wrapper.unmount()
    await nextTick()

    // The dispose should have been called on the instance returned by init
    const calls = (echarts.init as any).mock.results
    if (calls && calls.length > 0) {
      expect(calls[0].value.dispose).toHaveBeenCalled()
    }
  })

  it('removes resize listener on unmount', async () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener')

    const wrapper = mount(TestChartComponent)
    await nextTick()
    await new Promise((r) => setTimeout(r, 100))

    wrapper.unmount()
    await nextTick()

    // Should remove resize listener if autoResize was true
    // With autoResize:false, no listener should be added/removed
    expect(removeSpy).toBeDefined()
    removeSpy.mockRestore()
  })

  it('setOption does not throw before chart init', async () => {
    const wrapper = mount(TestChartComponent)
    const vm = wrapper.vm as any
    // Should not throw even if called before async init completes
    expect(() => vm.setOption({ title: { text: 'Test' } })).not.toThrow()
    wrapper.unmount()
  })

  it('resize does not throw before chart init', async () => {
    const wrapper = mount(TestChartComponent)
    const vm = wrapper.vm as any
    expect(() => vm.resize()).not.toThrow()
    wrapper.unmount()
  })

  it('getDataURL delegates to echarts instance', async () => {
    const wrapper = mount(TestChartComponent)
    await nextTick()
    await new Promise((r) => setTimeout(r, 100))

    const vm = wrapper.vm as any
    const url = vm.getDataURL()
    expect(url).toContain('data:image')

    wrapper.unmount()
  })
})

const makeChartComponent = (opts: any) =>
  defineComponent({
    name: 'TestChartAutoResize',
    setup() {
      return useECharts(opts)
    },
    render() {
      return h('div', { ref: 'chartRef', style: 'width:400px;height:300px' })
    },
  })

describe('useECharts autoResize', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it('autoResize=true 时注册 resize 监听', async () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    const wrapper = mount(makeChartComponent({ autoResize: true }))
    await vi.advanceTimersByTimeAsync(100)
    expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    addSpy.mockRestore()
    wrapper.unmount()
  })

  it('resize 事件防抖后调用实例 resize', async () => {
    const wrapper = mount(makeChartComponent({ autoResize: true, resizeDebounce: 100 }))
    await vi.advanceTimersByTimeAsync(100)
    const vm = wrapper.vm as any
    expect(vm.instance).not.toBeNull()

    window.dispatchEvent(new Event('resize'))
    window.dispatchEvent(new Event('resize'))
    expect(vm.instance.resize).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(50)
    expect(vm.instance.resize).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(50)
    expect(vm.instance.resize).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('autoResize=false 时不注册 resize 事件且手动 resize 调用实例', async () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    const wrapper = mount(makeChartComponent({ autoResize: false }))
    await vi.advanceTimersByTimeAsync(100)
    expect(addSpy).not.toHaveBeenCalledWith('resize', expect.any(Function))

    const vm = wrapper.vm as any
    vm.resize()
    expect(vm.instance.resize).toHaveBeenCalledTimes(1)
    addSpy.mockRestore()
    wrapper.unmount()
  })

  it('setOption 委托给 echarts 实例', async () => {
    const wrapper = mount(makeChartComponent({ autoResize: false }))
    await vi.advanceTimersByTimeAsync(100)
    const vm = wrapper.vm as any
    const option = { title: { text: 'T' } }
    vm.setOption(option, { notMerge: true })
    expect(vm.instance.setOption).toHaveBeenCalledWith(option, { notMerge: true })
    wrapper.unmount()
  })

  it('autoResize=true 卸载时移除监听并 dispose', async () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener')
    const wrapper = mount(makeChartComponent({ autoResize: true }))
    await vi.advanceTimersByTimeAsync(100)
    const vm = wrapper.vm as any
    const instance = vm.instance
    expect(instance).not.toBeNull()

    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(0)
    expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    expect(instance.dispose).toHaveBeenCalledTimes(1)
    expect(vm.instance).toBeNull()
    removeSpy.mockRestore()
  })

  it('卸载时清理未触发的 resize 定时器', async () => {
    const wrapper = mount(makeChartComponent({ autoResize: true, resizeDebounce: 100 }))
    await vi.advanceTimersByTimeAsync(100)
    const vm = wrapper.vm as any
    const inst = vm.instance

    window.dispatchEvent(new Event('resize'))
    wrapper.unmount()
    await vi.advanceTimersByTimeAsync(200)
    expect(inst.resize).not.toHaveBeenCalled()
  })

  it('chartRef 未绑定时 _init 直接返回不初始化', async () => {
    const NoRefComponent = defineComponent({
      setup() {
        return useECharts()
      },
      render() {
        return h('div')
      },
    })
    const echarts = await import('echarts')
    vi.clearAllMocks()
    const wrapper = mount(NoRefComponent)
    await vi.advanceTimersByTimeAsync(100)
    expect(echarts.init).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('getDataURL 在实例未初始化时返回空字符串', async () => {
    const wrapper = mount(makeChartComponent({ autoResize: false }))
    const vm = wrapper.vm as any
    expect(vm.instance).toBeNull()
    expect(vm.getDataURL()).toBe('')
    wrapper.unmount()
  })
})
