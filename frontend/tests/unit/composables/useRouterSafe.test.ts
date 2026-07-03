import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockPush = vi.fn()
const mockResolve = vi.fn(() => ({ name: 'TestRoute', matched: [{ path: '/test' }] }))
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, resolve: mockResolve }),
}))

import { useRouterSafe } from '@/composables/useRouterSafe'

describe('useRouterSafe', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('返回 pushSafe 函数', () => {
    const { pushSafe } = useRouterSafe()
    expect(typeof pushSafe).toBe('function')
  })

  it('pushSafe 调用 router.push with string path', () => {
    mockPush.mockReturnValueOnce(Promise.resolve())
    const { pushSafe } = useRouterSafe()
    pushSafe('/dashboard')
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('pushSafe 调用 router.push with route object', () => {
    mockPush.mockReturnValueOnce(Promise.resolve())
    const { pushSafe } = useRouterSafe()
    const route = { path: '/users', query: { id: 5 } }
    pushSafe(route)
    expect(mockPush).toHaveBeenCalledWith(route)
  })

  it('pushSafe 接受 debugLabel 参数 (无副作用)', () => {
    mockPush.mockReturnValueOnce(Promise.resolve())
    const { pushSafe } = useRouterSafe()
    pushSafe('/test', '测试页面')
    expect(mockPush).toHaveBeenCalledWith('/test')
  })

  it('pushSafe 失败时调用 window.location.href fallback', async () => {
    mockPush.mockReturnValueOnce(Promise.reject(new Error('nav failed')))
    const originalLocation = window.location
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, href: '' },
      writable: true,
    })
    const consoleErr = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { pushSafe } = useRouterSafe()
    pushSafe('/fallback')
    await new Promise((r) => setTimeout(r, 10))
    expect(consoleErr).toHaveBeenCalled()
    consoleErr.mockRestore()
  })

  it('pushSafe 同步异常时也 fallback 到 window.location.href', () => {
    mockPush.mockImplementationOnce(() => {
      throw new Error('sync')
    })
    const consoleErr = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { pushSafe } = useRouterSafe()
    pushSafe('/safe')
    expect(consoleErr).toHaveBeenCalled()
    consoleErr.mockRestore()
  })
})
