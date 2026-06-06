import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ChunkUploader, uploadFileWithChunks, resumeFileUpload } from '@/utils/chunkUpload'

// Mock fetch
const mockFetch = vi.fn()
;(globalThis as any).fetch = mockFetch

// Mock crypto.subtle.digest for jsdom (use Object.defineProperty to bypass getter)
const mockDigest = vi.fn()
try {
  ;(globalThis as any).crypto = (globalThis as any).crypto || {}
  ;(globalThis as any).crypto.subtle = (globalThis as any).crypto.subtle || {}
  Object.defineProperty((globalThis as any).crypto.subtle, 'digest', {
    value: mockDigest,
    writable: true,
    configurable: true,
  })
} catch {
  // jsdom might block; try via Reflect
  try {
    Object.defineProperty(globalThis, 'crypto', {
      value: { subtle: { digest: mockDigest } },
      configurable: true,
      writable: true,
    })
  } catch {}
}

function makeFile(sizeBytes: number, name = 'test.bin'): File {
  const buf = new ArrayBuffer(sizeBytes)
  return new File([buf], name, { type: 'application/octet-stream' })
}

function mockHashResponse() {
  mockDigest.mockResolvedValueOnce(new Uint8Array([0xde, 0xad, 0xbe, 0xef]).buffer)
}

const okJsonResponse = (data: any = {}) => ({
  ok: true,
  statusText: 'OK',
  json: () => Promise.resolve(data),
})

describe('utils/chunkUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetch.mockResolvedValue(okJsonResponse())
    mockHashResponse()
  })

  afterEach(() => { vi.clearAllMocks() })

  describe('ChunkUploader constructor', () => {
    it('默认 chunkSize = 5MB', () => {
      const file = makeFile(10 * 1024 * 1024)
      const u = new ChunkUploader({ file })
      const t = u as any
      expect(t.chunkSize).toBe(5 * 1024 * 1024)
    })

    it('自定义 chunkSize', () => {
      const file = makeFile(1024)
      const u = new ChunkUploader({ file, chunkSize: 256 })
      const t = u as any
      expect(t.chunkSize).toBe(256)
    })

    it('生成 fileId 含 timestamp + random', () => {
      const file = makeFile(1024)
      const u = new ChunkUploader({ file })
      const t = u as any
      expect(t.fileId).toMatch(/^\d+_[a-z0-9]+$/)
    })

    it('totalChunks = ceil(size / chunkSize)', () => {
      const file = makeFile(1000)
      const u = new ChunkUploader({ file, chunkSize: 100 })
      const t = u as any
      expect(t.totalChunks).toBe(10)
    })

    it('uploadedChunks 初始为空 Set', () => {
      const file = makeFile(1000)
      const u = new ChunkUploader({ file, chunkSize: 100 })
      const t = u as any
      expect(t.uploadedChunks).toBeInstanceOf(Set)
      expect(t.uploadedChunks.size).toBe(0)
    })
  })

  it('createChunk 用 file.slice', () => {
    const file = makeFile(100)
    const u = new ChunkUploader({ file, chunkSize: 30 })
    const c1 = (u as any).createChunk(0)
    const c2 = (u as any).createChunk(1)
    const c3 = (u as any).createChunk(3)  // last partial
    expect(c1.size).toBe(30)
    expect(c2.size).toBe(30)
    expect(c3.size).toBe(10)  // 100 - 90 = 10
  })

  it('getProgress 0 -> 100', async () => {
    const file = makeFile(200)
    const u = new ChunkUploader({ file, chunkSize: 100 })
    expect(u.getProgress()).toBe(0)
    ;(u as any).uploadedChunks.add(0)
    expect(u.getProgress()).toBe(50)
    ;(u as any).uploadedChunks.add(1)
    expect(u.getProgress()).toBe(100)
  })

  it('getUploadedChunks 返回数组', () => {
    const file = makeFile(100)
    const u = new ChunkUploader({ file, chunkSize: 50 })
    ;(u as any).uploadedChunks.add(0)
    expect(u.getUploadedChunks()).toEqual([0])
  })

  it('pause 是 no-op', () => {
    const file = makeFile(100)
    const u = new ChunkUploader({ file })
    u.pause()
  })

  it('cancel 清空 uploadedChunks', () => {
    const file = makeFile(100)
    const u = new ChunkUploader({ file, chunkSize: 50 })
    ;(u as any).uploadedChunks.add(0)
    u.cancel()
    expect(u.getUploadedChunks()).toEqual([])
  })

  it('upload 成功回调触发 onChunkComplete + onProgress + onComplete', async () => {
    const file = makeFile(200)
    const onProgress = vi.fn()
    const onChunkComplete = vi.fn()
    const onComplete = vi.fn()
    const u = new ChunkUploader({ file, chunkSize: 100, onProgress, onChunkComplete, onComplete })
    const result = await u.upload('/api/upload')
    expect(result.fileName).toBe('test.bin')
    expect(onChunkComplete).toHaveBeenCalledTimes(2)
    expect(onProgress).toHaveBeenLastCalledWith(100)
    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })

  it('upload 失败时 onError 触发并 throw', async () => {
    const file = makeFile(100)
    const onError = vi.fn()
    const u = new ChunkUploader({ file, chunkSize: 100, onError })
    mockFetch.mockRejectedValueOnce(new Error('network down'))
    await expect(u.upload('/api/upload')).rejects.toThrow('network down')
    expect(onError).toHaveBeenCalled()
  })

  it('upload fetch response.ok=false 抛错', async () => {
    const file = makeFile(100)
    const onError = vi.fn()
    const u = new ChunkUploader({ file, chunkSize: 100, onError })
    mockFetch.mockResolvedValueOnce({ ok: false, statusText: 'Internal Server Error' })
    await expect(u.upload('/api/upload')).rejects.toThrow(/分片上传失败/)
    expect(onError).toHaveBeenCalled()
  })

  it('upload 跳过已上传的分片 (uploadedChunks 初始非空)', async () => {
    const file = makeFile(200)
    const u = new ChunkUploader({ file, chunkSize: 100 })
    ;(u as any).uploadedChunks.add(0)  // skip first chunk
    await u.upload('/api/upload')
    // Only 1 fetch call (for chunk 1)
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('resumeUpload 复用 uploadedChunks', async () => {
    const file = makeFile(200)
    const u = new ChunkUploader({ file, chunkSize: 100 })
    ;(u as any).uploadedChunks.add(0)
    await u.resumeUpload('/api/upload')
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('uploadFormData 包含 chunk, chunkIndex, totalChunks, fileId, fileName, fileSize, fileHash', async () => {
    const file = makeFile(100)
    const u = new ChunkUploader({ file, chunkSize: 100 })
    await u.upload('/api/upload')
    const fd = mockFetch.mock.calls[0][1].body as FormData
    expect(fd).toBeInstanceOf(FormData)
    expect(fd.get('chunk')).toBeInstanceOf(Blob)
    expect(fd.get('chunkIndex')).toBe('0')
    expect(fd.get('totalChunks')).toBe('1')
    expect(fd.get('fileId')).toMatch(/^\d+_/)
    expect(fd.get('fileName')).toBe('test.bin')
    expect(fd.get('fileSize')).toBe('100')
    expect(fd.get('fileHash')).toBe('deadbeef')
  })

  it('uploadFileWithChunks 包装函数', async () => {
    const file = makeFile(100)
    const r = await uploadFileWithChunks(file, '/api/upload')
    expect(r.fileName).toBe('test.bin')
  })

  it('resumeFileUpload 用给定的 fileId + uploadedChunks', async () => {
    const file = makeFile(200)
    const r = await resumeFileUpload('FILE_1', [0], file, '/api/upload', { chunkSize: 100 })
    expect(r.fileId).toBe('FILE_1')
    // Only 1 fetch (chunk 1)
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('resumeUpload 失败时 onError 触发', async () => {
    const file = makeFile(100)
    const onError = vi.fn()
    mockFetch.mockRejectedValueOnce(new Error('fail'))
    const r = resumeFileUpload('F1', [], file, '/api/upload', { chunkSize: 100, onError })
    await expect(r).rejects.toThrow('fail')
    expect(onError).toHaveBeenCalled()
  })
})
