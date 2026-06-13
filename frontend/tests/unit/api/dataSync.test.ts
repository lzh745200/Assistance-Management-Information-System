import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('@/utils/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args), post: (...args: any[]) => mockPost(...args) },
}))

vi.mock('@/api/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args), post: (...args: any[]) => mockPost(...args) },
}))

import client from '@/api/client'
import {
  importData,
  importEncryptedData,
  exportData,
  exportEncryptedData,
  downloadExportPackage,
  getSyncLogs,
  getConflicts,
  resolveConflict,
  dataSyncApi,
} from '@/api/dataSync'

describe('api/client', () => {
  it('导出 request axios 实例', () => {
    expect(client).toBeDefined()
  })
})

describe('api/dataSync', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('importData POST /data-sync/import FormData 默认 overwrite', () => {
    const file = new File(['x'], 'a.zip')
    importData(file)
    const [url, fd, config] = mockPost.mock.calls[0]
    expect(url).toBe('/data-sync/import')
    expect(fd).toBeInstanceOf(FormData)
    expect(fd.get('file')).toBe(file)
    expect(fd.get('strategy')).toBe('overwrite')
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  it('importData 自定义 strategy', () => {
    importData(new File(['x'], 'a.zip'), 'merge')
    expect(mockPost.mock.calls[0][1].get('strategy')).toBe('merge')
  })

  it('importEncryptedData POST FormData 含 password', () => {
    const file = new File(['x'], 'a.zip')
    importEncryptedData(file, 'pwd')
    const [url, fd] = mockPost.mock.calls[0]
    expect(url).toBe('/data-sync/import-encrypted')
    expect(fd.get('file')).toBe(file)
    expect(fd.get('password')).toBe('pwd')
  })

  it('exportData POST /data-sync/export', () => {
    exportData({ foo: 1 })
    expect(mockPost).toHaveBeenCalledWith('/data-sync/export', { foo: 1 })
  })

  it('exportEncryptedData POST /data-sync/export-encrypted', () => {
    exportEncryptedData({ password: 'p', modules: ['village'] })
    expect(mockPost).toHaveBeenCalledWith('/data-sync/export-encrypted', {
      password: 'p',
      modules: ['village'],
    })
  })

  it('downloadExportPackage GET blob', async () => {
    mockGet.mockResolvedValueOnce({ data: new Blob(['x']) })
    await downloadExportPackage('XYZ')
    expect(mockGet).toHaveBeenCalledWith('/data-sync/export/download/XYZ', { responseType: 'blob' })
  })

  it('getSyncLogs GET /data-sync/logs', () => {
    getSyncLogs({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/data-sync/logs', { params: { page: 1 } })
  })

  it('getConflicts GET /data-sync/conflicts/{syncLogId}', () => {
    getConflicts(42)
    expect(mockGet).toHaveBeenCalledWith('/data-sync/conflicts/42')
  })

  it('resolveConflict POST /data-sync/resolve-conflict', () => {
    resolveConflict({ conflict_id: 1, resolution: 'overwrite' })
    expect(mockPost).toHaveBeenCalledWith('/data-sync/resolve-conflict', {
      conflict_id: 1,
      resolution: 'overwrite',
    })
  })

  it('dataSyncApi.importData/importEncryptedData/exportData/exportEncryptedData 转发', () => {
    const f = new File(['x'], 'a.zip')
    dataSyncApi.importData(f)
    dataSyncApi.importEncryptedData(f, 'p')
    dataSyncApi.exportData({ a: 1 })
    dataSyncApi.exportEncryptedData({ password: 'p' })
    expect(mockPost).toHaveBeenCalledTimes(4)
  })

  it('dataSyncApi.getSyncLogs/getConflicts/resolveConflict/downloadExportPackage 转发', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [] } })
    mockGet.mockResolvedValueOnce({ data: [] })
    dataSyncApi.getSyncLogs()
    dataSyncApi.getConflicts(10)
    dataSyncApi.resolveConflict({ conflict_id: 2, resolution: 'skip' })
    expect(mockGet).toHaveBeenCalledWith('/data-sync/logs', { params: undefined })
    expect(mockGet).toHaveBeenCalledWith('/data-sync/conflicts/10')
    expect(mockPost).toHaveBeenCalledWith('/data-sync/resolve-conflict', {
      conflict_id: 2,
      resolution: 'skip',
    })
  })
})
