import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockDrive = vi.fn()
const mockDriver = vi.fn(() => ({ drive: mockDrive }))

vi.mock('driver.js', () => ({
  driver: (...args: any[]) => mockDriver(...args),
}))

vi.mock('driver.js/dist/driver.css', () => ({}))

import { useOnboarding } from '@/composables/useOnboarding'

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
