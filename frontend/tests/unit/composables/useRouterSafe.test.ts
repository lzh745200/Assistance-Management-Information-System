import { describe, it, expect, beforeEach, vi } from 'vitest'

const mockPush = vi.fn()
const mockResolve = vi.fn(() => ({ name: 'TestRoute', matched: [{ path: '/test' }] }))
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, resolve: mockResolve }),
}))

import { useRouterSafe, safeRouteParam } from '@/composables/useRouterSafe'

describe('safeRouteParam', () => {
  it('undefined → 默认回退值', () => {
    expect(safeRouteParam(undefined)).toBe(0)
    expect(safeRouteParam(undefined, 9)).toBe(9)
  })

  it('null → 默认回退值', () => {
    expect(safeRouteParam(null, 9)).toBe(9)
  })

  it('数字字符串 → 转数字', () => {
    expect(safeRouteParam('42')).toBe(42)
    expect(safeRouteParam('3.5', 9)).toBe(3.5)
  })

  it('无效字符串 → 回退值', () => {
    expect(safeRouteParam('abc', 9)).toBe(9)
  })

  it('数字值 → 直接返回', () => {
    expect(safeRouteParam(7)).toBe(7)
  })

  it('Infinity/NaN → 回退值', () => {
    expect(safeRouteParam(Infinity, 9)).toBe(9)
    expect(safeRouteParam(NaN, 9)).toBe(9)
  })

  it('数组取第一个有效值', () => {
    expect(safeRouteParam(['5'])).toBe(5)
    expect(safeRouteParam(['7', '8'])).toBe(7)
  })

  it('空数组 → 回退值', () => {
    expect(safeRouteParam([], 9)).toBe(9)
  })

  it('数组首元素为 null → 回退值', () => {
    expect(safeRouteParam([null], 9)).toBe(9)
  })

  it('数组内为无效值 → 回退值', () => {
    expect(safeRouteParam(['x'], 9)).toBe(9)
  })
})

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

  it('非 DEV 环境 debugLabel 不输出日志', () => {
    vi.stubEnv('DEV', false)
    const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    mockPush.mockReturnValueOnce(Promise.resolve())
    const { pushSafe } = useRouterSafe()
    pushSafe('/test', '测试页面')
    expect(logSpy).not.toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/test')
    logSpy.mockRestore()
    vi.unstubAllEnvs()
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

  it('路由解析为 NotFound 时 console.error 并回退原生跳转', () => {
    mockResolve.mockReturnValueOnce({ name: 'NotFound', matched: [{ path: '/x' }] })
    const originalLocation = window.location
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, href: '' },
      writable: true,
    })
    const consoleErr = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { pushSafe } = useRouterSafe()
    pushSafe('/unknown', '未知路由')
    expect(consoleErr).toHaveBeenCalledWith(
      expect.stringContaining('/unknown (未知路由)')
    )
    expect(window.location.href).toBe('/unknown')
    expect(mockPush).not.toHaveBeenCalled()
    consoleErr.mockRestore()
  })

  it('路由解析 matched 为空时回退原生跳转', () => {
    mockResolve.mockReturnValueOnce({ name: 'X', matched: [] })
    const originalLocation = window.location
    Object.defineProperty(window, 'location', {
      value: { ...originalLocation, href: '' },
      writable: true,
    })
    const consoleErr = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { pushSafe } = useRouterSafe()
    pushSafe('/void')
    expect(consoleErr).toHaveBeenCalled()
    expect(window.location.href).toBe('/void')
    consoleErr.mockRestore()
  })

  it('路由对象无 path 时跳过解析检查并正常 push', () => {
    mockPush.mockReturnValueOnce(Promise.resolve())
    const { pushSafe } = useRouterSafe()
    const route = { name: 'SomeNamedRoute', params: { id: 1 } }
    pushSafe(route)
    expect(mockPush).toHaveBeenCalledWith(route)
  })

  it('push 返回非 Promise 时不抛错', () => {
    mockPush.mockReturnValueOnce(undefined as any)
    const { pushSafe } = useRouterSafe()
    expect(() => pushSafe('/no-promise')).not.toThrow()
  })

  it('路由对象无 path 且 push 同步抛错时不回退原生跳转', () => {
    mockPush.mockImplementationOnce(() => {
      throw new Error('sync')
    })
    const consoleErr = vi.spyOn(console, 'error').mockImplementation(() => {})
    const hrefSpy = vi.spyOn(window.location, 'href' as any, 'set')
    const { pushSafe } = useRouterSafe()
    pushSafe({ name: 'NamedRoute' })
    expect(consoleErr).toHaveBeenCalled()
    expect(hrefSpy).not.toHaveBeenCalled()
    consoleErr.mockRestore()
    hrefSpy.mockRestore()
  })

  it('路由对象无 path 且 push 异步失败时不回退原生跳转', async () => {
    mockPush.mockReturnValueOnce(Promise.reject(new Error('async')))
    const consoleErr = vi.spyOn(console, 'error').mockImplementation(() => {})
    const hrefSpy = vi.spyOn(window.location, 'href' as any, 'set')
    const { pushSafe } = useRouterSafe()
    pushSafe({ name: 'NamedRoute' })
    await new Promise((r) => setTimeout(r, 10))
    expect(consoleErr).toHaveBeenCalled()
    expect(hrefSpy).not.toHaveBeenCalled()
    consoleErr.mockRestore()
    hrefSpy.mockRestore()
  })
})
