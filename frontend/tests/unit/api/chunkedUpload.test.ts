import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost, mockDel } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDel: vi.fn(),
}))

// src/api/chunkedUpload.ts 实际 import：import { get, post, del } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  del: mockDel,
}))

import {
  initChunkedUpload,
  uploadChunk,
  getChunkedUploadProgress,
  mergeChunkedUpload,
  cancelChunkedUpload,
} from '@/api/chunkedUpload'

describe('api/chunkedUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initChunkedUpload 调用 POST /chunked-upload/init 并透传载荷', async () => {
    const body = {
      session_id: 's1',
      file_name: 'a.zip',
      file_size: 100,
      chunk_size: 10,
      total_chunks: 10,
      status: 'init',
    }
    mockPost.mockResolvedValue(body)
    const data = { file_name: 'a.zip', file_size: 100, chunk_size: 10 }
    const result = await initChunkedUpload(data)
    expect(mockPost).toHaveBeenCalledWith('/chunked-upload/init', data)
    expect(result).toBe(body)
  })

  it('uploadChunk 以 FormData 形式上传分片（无 chunkHash）', async () => {
    const body = { success: true, chunk_index: 0 }
    mockPost.mockResolvedValue(body)
    const blob = new Blob(['chunk-data'])
    const result = await uploadChunk('s1', 0, blob)
    expect(mockPost).toHaveBeenCalledTimes(1)
    const [url, formData] = mockPost.mock.calls[0]
    expect(url).toBe('/chunked-upload/chunk/s1/0')
    expect(formData).toBeInstanceOf(FormData)
    // jsdom 的 FormData.append 会把 Blob 包装成 File，断言内容而非对象同一性
    const file = formData.get('file') as Blob
    expect(file.size).toBe(blob.size)
    expect(result).toBe(body)
  })

  it('uploadChunk 带 chunkHash 时追加 encodeURIComponent 查询参数', async () => {
    mockPost.mockResolvedValue({ success: true, chunk_index: 1 })
    const blob = new Blob(['x'])
    await uploadChunk('s1', 1, blob, '哈希+abc')
    const [url, formData] = mockPost.mock.calls[0]
    expect(url).toBe(`/chunked-upload/chunk/s1/1?chunk_hash=${encodeURIComponent('哈希+abc')}`)
    expect(formData).toBeInstanceOf(FormData)
    const file = formData.get('file') as Blob
    expect(file.size).toBe(blob.size)
  })

  it('getChunkedUploadProgress 调用 GET /chunked-upload/progress/{sessionId}', async () => {
    const body = { session_id: 's1', progress: 50, status: 'uploading' }
    mockGet.mockResolvedValue(body)
    const result = await getChunkedUploadProgress('s1')
    expect(mockGet).toHaveBeenCalledWith('/chunked-upload/progress/s1')
    expect(result).toBe(body)
  })

  it('mergeChunkedUpload 调用 POST /chunked-upload/merge/{sessionId}', async () => {
    const body = { session_id: 's1', file_path: '/uploads/a.zip', status: 'merged' }
    mockPost.mockResolvedValue(body)
    const result = await mergeChunkedUpload('s1')
    expect(mockPost).toHaveBeenCalledWith('/chunked-upload/merge/s1')
    expect(result).toBe(body)
  })

  it('cancelChunkedUpload 调用 DELETE /chunked-upload/{sessionId}', async () => {
    mockDel.mockResolvedValue({ success: true })
    await cancelChunkedUpload('s1')
    expect(mockDel).toHaveBeenCalledWith('/chunked-upload/s1')
  })
})
