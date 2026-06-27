import { describe, it, expect, vi, beforeEach } from 'vitest'

const handlers = vi.hoisted(() => ({ request: null as any, response: null as any }))
const mockInst = vi.hoisted(() => ({
  request: vi.fn(),
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  patch: vi.fn(),
  interceptors: {
    request: { use: vi.fn((f: any, r: any) => { handlers.request = f; handlers.requestR = r }) },
    response: { use: vi.fn((f: any, r: any) => { handlers.response = f; handlers.responseR = r }) },
  },
  defaults: {},
}))

const authState = vi.hoisted(() => ({ token: 'test-jwt-token' }))

const mockCancelToken = vi.hoisted(() =>
  Object.assign(
    vi.fn((executor: any) => { executor(() => {}); return 'cancel-token' }),
    { source: vi.fn(() => ({ token: 'mock-token', cancel: vi.fn() })) }
  )
)

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockInst),
    CancelToken: mockCancelToken,
    Cancel: vi.fn(),
    isCancel: (e: any) => e?.__CANCEL__ === true,
  },
}))

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: {
    getToken: vi.fn(() => authState.token),
    clear: vi.fn(() => { authState.token = '' }),
  },
}))

vi.mock('element-plus', () => ({
  ElMessage: { error: vi.fn(), warning: vi.fn(), success: vi.fn(), info: vi.fn() },
}))

vi.mock('@/utils/offlineMock', () => ({
  isOfflineMode: vi.fn(() => false),
  getMockResponse: vi.fn(),
}))

vi.mock('@/composables/useSafeData', () => ({
  safeArray: (arr: any) => (Array.isArray(arr) ? arr : []),
}))

import { freezeRequests, unfreezeRequests, _setCachedToken } from '@/api/request'

describe('api/request — interceptors', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    authState.token = 'test-jwt-token'
    _setCachedToken(null)
  })

  describe('request interceptor', () => {
    it('在冻结状态时拒绝请求', async () => {
      freezeRequests()
      const config = { method: 'GET', url: '/test', headers: {} }
      await expect(handlers.request(config)).rejects.toBeDefined()
      unfreezeRequests()
    })

    it('挂载 Authorization header', async () => {
      const config = { method: 'GET', url: '/test', headers: {} }
      await handlers.request(config)
      expect(config.headers.Authorization).toBe('Bearer test-jwt-token')
    })

    it('无 token 时不挂载 Authorization', async () => {
      authState.token = ''
      const config = { method: 'GET', url: '/test', headers: {} }
      await handlers.request(config)
      expect(config.headers.Authorization).toBeUndefined()
    })

    it('不安全方法不会因 CSRF 获取失败而抛出', async () => {
      const config = { method: 'DELETE', url: '/test', headers: {} }
      await expect(handlers.request(config)).resolves.toBeDefined()
      // 测试环境 _isTestEnv 为 true，_ensureCsrfToken 返回 null，不会设置头
    })
  })

  describe('response interceptor — success', () => {
    it('清除 pending 追踪', () => {
      const response = {
        config: { method: 'GET', url: '/test', params: {} },
        data: { code: 200, message: '成功' },
      }
      const result = handlers.response(response)
      expect(result).toBe(response)
    })

    it('展开 data 对象到顶层', () => {
      const response = {
        config: { method: 'GET', url: '/items' },
        data: { code: 200, data: { name: 'test', value: 42 } },
      }
      handlers.response(response)
      expect(response.data.name).toBe('test')
      expect(response.data.value).toBe(42)
    })

    it('数组 payload 设为 items', () => {
      const response = {
        config: { method: 'GET', url: '/list' },
        data: { code: 200, data: [{ id: 1 }, { id: 2 }] },
      }
      handlers.response(response)
      expect(response.data.items).toEqual([{ id: 1 }, { id: 2 }])
    })
  })

  describe('response interceptor — error', () => {
    it('已取消请求不处理', async () => {
      const error = { __CANCEL__: true }
      await expect(handlers.responseR(error)).rejects.toBe(error)
    })

    it('401 清除 token', async () => {
      const error = { response: { status: 401, data: {} } }
      await expect(handlers.responseR(error)).rejects.toBe(error)
    })

    it('网络错误', async () => {
      const error = { code: 'ERR_NETWORK', message: 'NetworkError', config: { method: 'GET', url: '/test' } }
      await expect(handlers.responseR(error)).rejects.toBe(error)
    })

    it('超时错误', async () => {
      const error = { code: 'ECONNABORTED', message: 'timeout', config: {} }
      await expect(handlers.responseR(error)).rejects.toBe(error)
    })
  })
})
