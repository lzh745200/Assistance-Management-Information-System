import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'

const mockDrive = vi.fn()
const mockDriver = vi.fn(() => ({ drive: mockDrive }))

vi.mock('driver.js', () => ({
  driver: (...args: any[]) => mockDriver(...args),
}))

vi.mock('driver.js/dist/driver.css', () => ({}))

import { useOnboarding } from '@/composables/useOnboarding'

const makeOnboardingComponent = (opts?: { force?: boolean }) =>
  defineComponent({
    name: 'OnboardingHost',
    setup() {
      return useOnboarding(opts)
    },
    render() {
      return h('div')
    },
  })

describe('useOnboarding', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('返回 startTour 函数', () => {
    const { startTour } = useOnboarding()
    expect(typeof startTour).toBe('function')
  })

  it('startTour 调用 driver() 和 drive()', () => {
    const { startTour } = useOnboarding()
    startTour()
    expect(mockDriver).toHaveBeenCalled()
    expect(mockDrive).toHaveBeenCalled()
  })

  it('startTour 传入 dashboardSteps 作为 steps 配置', () => {
    const { startTour } = useOnboarding()
    startTour()
    const config = mockDriver.mock.calls[0][0]
    expect(Array.isArray(config.steps)).toBe(true)
    expect(config.steps.length).toBeGreaterThan(0)
  })

  it('startTour 配置 showProgress=true', () => {
    const { startTour } = useOnboarding()
    startTour()
    const config = mockDriver.mock.calls[0][0]
    expect(config.showProgress).toBe(true)
  })

  it('startTour 配置包含中文按钮文本', () => {
    const { startTour } = useOnboarding()
    startTour()
    const config = mockDriver.mock.calls[0][0]
    expect(config.nextBtnText).toBe('下一步')
    expect(config.prevBtnText).toBe('上一步')
    expect(config.doneBtnText).toBe('完成')
  })

  it('onDestroyed 时写入 localStorage 标记', () => {
    const { startTour } = useOnboarding()
    startTour()
    const config = mockDriver.mock.calls[0][0]
    expect(typeof config.onDestroyed).toBe('function')

    config.onDestroyed()
    const stored = localStorage.getItem('onboarding_completed')
    expect(stored).toBeTruthy()
    const parsed = JSON.parse(stored!)
    expect(parsed.version).toBe(2)
    expect(typeof parsed.completedAt).toBe('number')
  })

  it('force=true 时 useOnboarding 仍正常返回 startTour', () => {
    const { startTour } = useOnboarding({ force: true })
    startTour()
    expect(mockDrive).toHaveBeenCalled()
  })

  it('options 为空时也返回 startTour', () => {
    const { startTour } = useOnboarding()
    startTour()
    expect(mockDrive).toHaveBeenCalled()
  })
})

describe('useOnboarding onMounted 行为', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('无完成标记时 onMounted 后延迟启动引导', async () => {
    const wrapper = mount(makeOnboardingComponent())
    expect(mockDrive).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(800)
    expect(mockDrive).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('已标记完成且版本一致时不启动引导', async () => {
    localStorage.setItem(
      'onboarding_completed',
      JSON.stringify({ version: 2, completedAt: Date.now() })
    )
    const wrapper = mount(makeOnboardingComponent())
    await vi.advanceTimersByTimeAsync(1000)
    expect(mockDrive).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('版本不一致时重新启动引导', async () => {
    localStorage.setItem(
      'onboarding_completed',
      JSON.stringify({ version: 1, completedAt: Date.now() })
    )
    const wrapper = mount(makeOnboardingComponent())
    await vi.advanceTimersByTimeAsync(800)
    expect(mockDrive).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('完成标记为损坏 JSON 时按未完成处理', async () => {
    localStorage.setItem('onboarding_completed', '{bad json')
    const wrapper = mount(makeOnboardingComponent())
    await vi.advanceTimersByTimeAsync(800)
    expect(mockDrive).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('force=true 时忽略完成标记强制引导', async () => {
    localStorage.setItem(
      'onboarding_completed',
      JSON.stringify({ version: 2, completedAt: Date.now() })
    )
    const wrapper = mount(makeOnboardingComponent({ force: true }))
    await vi.advanceTimersByTimeAsync(800)
    expect(mockDrive).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
