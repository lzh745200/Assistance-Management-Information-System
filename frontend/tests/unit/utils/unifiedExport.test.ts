import { describe, it, expect, vi, beforeEach } from 'vitest'

const { downloadBlobAsFile, requestGet } = vi.hoisted(() => ({
  downloadBlobAsFile: vi.fn(),
  requestGet: vi.fn(),
}))

vi.mock('@/api/helpers/blobDownload', () => ({ downloadBlobAsFile }))

vi.mock('@/api/request', () => ({
  default: { get: (...args: any[]) => requestGet(...args) },
}))

import { unifiedExport, exportUtil } from '@/utils/unifiedExport'

describe('utils/unifiedExport', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    downloadBlobAsFile.mockImplementation(async (requestFn: any) => {
      await requestFn()
    })
  })

  it('re-exports exportUtil', () => {
    expect(exportUtil).toBeDefined()
    expect(typeof exportUtil.exportToExcel).toBe('function')
  })

  it('默认格式 xlsx', async () => {
    await unifiedExport({ url: '/funds/export', params: { status: '1' }, fileName: '经费' })
    expect(requestGet).toHaveBeenCalledWith('/funds/export', {
      params: { status: '1', format: 'xlsx' },
      responseType: 'blob',
    })
    expect(downloadBlobAsFile).toHaveBeenCalledWith(expect.any(Function), {
      fallbackFileName: '经费.xlsx',
    })
  })

  it('csv 格式使用 .csv 扩展名', async () => {
    await unifiedExport({ url: '/funds/export', fileName: '名单', format: 'csv' })
    expect(requestGet).toHaveBeenCalledWith('/funds/export', {
      params: { format: 'csv' },
      responseType: 'blob',
    })
    expect(downloadBlobAsFile).toHaveBeenCalledWith(expect.any(Function), {
      fallbackFileName: '名单.csv',
    })
  })

  it('pdf 格式使用 .pdf 扩展名', async () => {
    await unifiedExport({ url: '/report', fileName: '报告', format: 'pdf' })
    expect(requestGet).toHaveBeenCalledWith('/report', {
      params: { format: 'pdf' },
      responseType: 'blob',
    })
    expect(downloadBlobAsFile).toHaveBeenCalledWith(expect.any(Function), {
      fallbackFileName: '报告.pdf',
    })
  })

  it('无 params 时不传额外参数', async () => {
    await unifiedExport({ url: '/x', fileName: 'f' })
    expect(requestGet).toHaveBeenCalledWith('/x', {
      params: { format: 'xlsx' },
      responseType: 'blob',
    })
  })
})
