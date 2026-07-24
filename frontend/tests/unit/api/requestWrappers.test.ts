import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// request.ts 本体测试：不 mock '@/api/request' 自身，改 mock 其底层 axios。
// apiRequest/get/post/put/del/patch 最终都走 axios 实例的 request()。
const { mockRequest, mockCancel, mockCancelSource } = vi.hoisted(() => {
  const mockRequest = vi.fn()
  const mockCancel = vi.fn()
  return {
    mockRequest,
    mockCancel,
    mockCancelSource: vi.fn(() => ({ token: 'mock-cancel-token', cancel: mockCancel })),
  }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      request: mockRequest,
      get: mockRequest,
      post: mockRequest,
      put: mockRequest,
      delete: mockRequest,
      patch: mockRequest,
      interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
      defaults: {},
    })),
    CancelToken: { source: mockCancelSource },
    Cancel: class Cancel {},
    isCancel: (e: any) => e?.__CANCEL__ === true,
  },
}))

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: { getToken: vi.fn(() => null), clear: vi.fn() },
}))

vi.mock('@/utils/offlineMock', () => ({
  isOfflineMode: vi.fn(() => false),
  getMockResponse: vi.fn(),
}))

import {
  apiRequest,
  get,
  post,
  put,
  del,
  patch,
  createCancelableRequest,
  requestWithTimeout,
  parseContentDisposition,
  downloadBlob,
} from '@/api/request'

describe('api/request — 封装方法参数透传', () => {
  beforeEach(() => vi.clearAllMocks())

  it('apiRequest 透传 config 并返回 res.data', async () => {
    const body = { items: [1, 2] }
    mockRequest.mockResolvedValueOnce({ data: body })
    const config = { method: 'GET', url: '/anything' }
    const result = await apiRequest(config)
    expect(mockRequest).toHaveBeenCalledWith(config)
    expect(result).toBe(body)
  })

  it('get(url, params) → GET + params，返回已解包 body', async () => {
    mockRequest.mockResolvedValueOnce({ data: ['a'] })
    const result = await get('/list', { page: 1 })
    expect(mockRequest).toHaveBeenCalledWith({ method: 'GET', url: '/list', params: { page: 1 } })
    expect(result).toEqual(['a'])
  })

  it('get(url) 无参数时 params 为 undefined', async () => {
    mockRequest.mockResolvedValueOnce({ data: {} })
    await get('/list')
    expect(mockRequest).toHaveBeenCalledWith({ method: 'GET', url: '/list', params: undefined })
  })

  it('post(url, data) → POST + data', async () => {
    mockRequest.mockResolvedValueOnce({ data: { id: 1 } })
    const result = await post('/items', { name: 'n' })
    expect(mockRequest).toHaveBeenCalledWith({ method: 'POST', url: '/items', data: { name: 'n' } })
    expect(result).toEqual({ id: 1 })
  })

  it('post(url, data, extra) 合并 extra 配置', async () => {
    mockRequest.mockResolvedValueOnce({ data: {} })
    await post('/items', { a: 1 }, { timeout: 5000, headers: { 'X-Custom': 'v' } })
    expect(mockRequest).toHaveBeenCalledWith({
      method: 'POST',
      url: '/items',
      data: { a: 1 },
      timeout: 5000,
      headers: { 'X-Custom': 'v' },
    })
  })

  it('post FormData 时移除 Content-Type（保留其他 headers）', async () => {
    mockRequest.mockResolvedValueOnce({ data: {} })
    const fd = new FormData()
    fd.append('file', new File(['x'], 'a.xlsx'))
    await post('/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data', 'X-Keep': 'yes' },
    })
    const config = mockRequest.mock.calls[0][0]
    expect(config.data).toBe(fd)
    expect(config.headers['Content-Type']).toBeUndefined()
    expect(config.headers['content-type']).toBeUndefined()
    expect(config.headers['X-Keep']).toBe('yes')
  })

  it('put(url, data) → PUT + data', async () => {
    mockRequest.mockResolvedValueOnce({ data: { ok: true } })
    const result = await put('/items/1', { name: 'n2' })
    expect(mockRequest).toHaveBeenCalledWith({
      method: 'PUT',
      url: '/items/1',
      data: { name: 'n2' },
    })
    expect(result).toEqual({ ok: true })
  })

  it('del(url) → DELETE', async () => {
    mockRequest.mockResolvedValueOnce({ data: { deleted: true } })
    const result = await del('/items/1')
    expect(mockRequest).toHaveBeenCalledWith({ method: 'DELETE', url: '/items/1' })
    expect(result).toEqual({ deleted: true })
  })

  it('patch(url, data) → PATCH + data', async () => {
    mockRequest.mockResolvedValueOnce({ data: { patched: true } })
    const result = await patch('/items/1', { flag: 1 })
    expect(mockRequest).toHaveBeenCalledWith({
      method: 'PATCH',
      url: '/items/1',
      data: { flag: 1 },
    })
    expect(result).toEqual({ patched: true })
  })
})

describe('api/request — 取消与超时', () => {
  beforeEach(() => vi.clearAllMocks())

  it('createCancelableRequest 返回 promise 与 cancel，并带上 cancelToken', async () => {
    mockRequest.mockResolvedValueOnce({ data: 'done' })
    const { promise, cancel } = createCancelableRequest({ method: 'GET', url: '/c' })
    expect(mockCancelSource).toHaveBeenCalled()
    expect(mockRequest).toHaveBeenCalledWith({
      method: 'GET',
      url: '/c',
      cancelToken: 'mock-cancel-token',
    })
    expect(cancel).toBe(mockCancel)
    await expect(promise).resolves.toBe('done')
  })

  it('requestWithTimeout 在超时内完成则正常返回', async () => {
    mockRequest.mockResolvedValueOnce({ data: 'fast' })
    const result = await requestWithTimeout({ method: 'GET', url: '/t' }, 5000)
    expect(result).toBe('fast')
  })

  it('requestWithTimeout 超时后取消请求并拒绝', async () => {
    vi.useFakeTimers()
    try {
      mockRequest.mockReturnValueOnce(new Promise(() => {}))
      const promise = requestWithTimeout({ method: 'GET', url: '/slow' }, 1000)
      const assertion = expect(promise).rejects.toThrow('Request timeout after 1000ms')
      await vi.advanceTimersByTimeAsync(1000)
      await assertion
      expect(mockCancel).toHaveBeenCalled()
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('api/request — parseContentDisposition', () => {
  it('无 headers 返回 fallback', () => {
    expect(parseContentDisposition(undefined)).toBe('download.xlsx')
    expect(parseContentDisposition(undefined, 'a.csv')).toBe('a.csv')
  })

  it('无 content-disposition 返回 fallback', () => {
    expect(parseContentDisposition({ 'content-type': 'text/plain' })).toBe('download.xlsx')
  })

  it('解析 RFC 5987 filename*（小写头）', () => {
    const encoded = encodeURIComponent('帮扶村.xlsx')
    const headers = { 'content-disposition': `attachment; filename*=UTF-8''${encoded}` }
    expect(parseContentDisposition(headers)).toBe('帮扶村.xlsx')
  })

  it('解析 RFC 5987 filename*（大写头键）', () => {
    const encoded = encodeURIComponent('学校名单.xlsx')
    const headers = { 'Content-Disposition': `attachment; filename*=UTF-8''${encoded}` }
    expect(parseContentDisposition(headers)).toBe('学校名单.xlsx')
  })

  it('回退解析 filename="quoted"', () => {
    const headers = { 'content-disposition': 'attachment; filename="report.xlsx"' }
    expect(parseContentDisposition(headers)).toBe('report.xlsx')
  })

  it('回退解析 filename=plain（无引号）', () => {
    const headers = { 'content-disposition': 'attachment; filename=data.csv' }
    expect(parseContentDisposition(headers)).toBe('data.csv')
  })

  it('filename* 解码失败时回退 filename= 或 fallback', () => {
    const headers = {
      'content-disposition': 'attachment; filename*=UTF-8\'\'%E4%B8%AD%ZZ; filename="safe.xlsx"',
    }
    // %ZZ 解码抛错 → 走 quoted 分支
    expect(parseContentDisposition(headers)).toBe('safe.xlsx')
  })

  it('全部解析失败返回 fallback', () => {
    const headers = { 'content-disposition': 'attachment' }
    expect(parseContentDisposition(headers, 'fb.bin')).toBe('fb.bin')
  })
})

describe('api/request — downloadBlob', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('创建 a 标签触发点击下载并释放 objectURL', () => {
    vi.useFakeTimers()
    const createObjectURL = vi.fn(() => 'blob:mock-url')
    const revokeObjectURL = vi.fn()
    ;(window.URL as any).createObjectURL = createObjectURL
    ;(window.URL as any).revokeObjectURL = revokeObjectURL

    const link = document.createElement('a')
    link.click = vi.fn()
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: any) =>
      tag === 'a' ? link : realCreate(tag)
    )

    const blob = new Blob(['x'])
    downloadBlob(blob, '导出.xlsx')

    expect(createObjectURL).toHaveBeenCalledWith(blob)
    expect(link.href).toBe('blob:mock-url')
    expect(link.download).toBe('导出.xlsx')
    expect(link.style.display).toBe('none')
    expect(link.click).toHaveBeenCalled()

    vi.advanceTimersByTime(150)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    expect(document.body.contains(link)).toBe(false)
  })
})
