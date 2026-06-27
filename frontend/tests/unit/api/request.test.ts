import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockAxiosRequest = vi.hoisted(() => vi.fn())
const mockAxiosCreate = vi.hoisted(() => vi.fn(() => ({
  get: mockAxiosRequest,
  post: mockAxiosRequest,
  put: mockAxiosRequest,
  delete: mockAxiosRequest,
  patch: mockAxiosRequest,
  request: mockAxiosRequest,
  interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  defaults: {},
})))

vi.mock('axios', () => ({
  default: {
    create: mockAxiosCreate,
    CancelToken: { source: () => ({ token: 'mock-token', cancel: vi.fn() }) },
    isCancel: (e: any) => e?.__CANCEL__ === true,
  },
}))

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: {
    getToken: vi.fn(() => null),
    clear: vi.fn(),
  },
}))

vi.mock('@/utils/offlineMock', () => ({
  isOfflineMode: vi.fn(() => false),
  getMockResponse: vi.fn(),
}))

import {
  isSuccess,
  freezeRequests,
  unfreezeRequests,
  isRequestCancelled,
  getPendingRequestCount,
  cancelRequest,
  cancelAllRequests,
  _setCachedToken,
  prefetchCsrfToken,
} from '@/api/request'

describe('api/request — utility', () => {
  it('isSuccess 返回 true 对 2xx', () => {
    expect(isSuccess(200)).toBe(true)
    expect(isSuccess(201)).toBe(true)
    expect(isSuccess(299)).toBe(true)
  })

  it('isSuccess 返回 false 对 非 2xx', () => {
    expect(isSuccess(400)).toBe(false)
    expect(isSuccess(401)).toBe(false)
    expect(isSuccess(500)).toBe(false)
  })

  it('freezeRequests / unfreezeRequests', () => {
    freezeRequests()
    freezeRequests()
    unfreezeRequests()
  })

  it('isRequestCancelled', () => {
    expect(isRequestCancelled({ __CANCEL__: true })).toBe(true)
    expect(isRequestCancelled({})).toBe(false)
    expect(isRequestCancelled(null)).toBe(false)
  })

  it('getPendingRequestCount', () => {
    expect(getPendingRequestCount()).toBe(0)
  })

  it('cancelRequest / cancelAllRequests', () => {
    cancelRequest('/test')
    cancelAllRequests()
  })

  it('_setCachedToken', () => {
    _setCachedToken('new-token')
    _setCachedToken(null)
  })

  it('prefetchCsrfToken 在测试环境返回 null', async () => {
    const result = await prefetchCsrfToken()
    expect(result).toBeNull()
  })
})
