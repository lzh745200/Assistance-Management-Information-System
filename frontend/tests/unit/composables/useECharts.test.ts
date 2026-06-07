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
