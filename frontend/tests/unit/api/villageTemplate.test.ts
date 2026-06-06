import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()

vi.mock('@/utils/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args) },
}))
vi.mock('@/api/request', () => ({
  default: { get: (...args: any[]) => mockGet(...args) },
  get: (...args: any[]) => mockGet(...args),
}))

import {
  getTemplateList,
  downloadTemplate,
  getStaticTemplateModules,
  getTemplateInfoByModule,
} from '@/api/villageTemplate'

describe('api/villageTemplate', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getTemplateList GET /templates', async () => {
    mockGet.mockResolvedValueOnce({ total: 12, templates: [] })
    await getTemplateList()
    expect(mockGet).toHaveBeenCalledWith('/templates')
  })

  it('downloadTemplate 默认 include_example=true 触发下载', async () => {
    mockGet.mockResolvedValueOnce({
      data: new Blob(['x']),
      headers: { 'content-disposition': '' },
    })
    const click = vi.fn()
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
      if (tag === 'a') return Object.assign(realCreate(tag), { click })
      return realCreate(tag)
    })
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:fake')
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    await downloadTemplate('village')
    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('/templates/village?'),
      { responseType: 'blob' },
    )
    const urlArg = mockGet.mock.calls[0][0]
    expect(urlArg).toContain('include_example=true')
    expect(click).toHaveBeenCalled()
  })

  it('downloadTemplate 带 year 和 includeExample=false', async () => {
    mockGet.mockResolvedValueOnce({
      data: new Blob(['x']),
      headers: {},
    })
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
      if (tag === 'a') return Object.assign(realCreate(tag), { click: vi.fn() })
      return realCreate(tag)
    })
    await downloadTemplate('population', { year: 2026, includeExample: false })
    const urlArg = mockGet.mock.calls[0][0]
    expect(urlArg).toContain('year=2026')
    expect(urlArg).toContain('include_example=false')
  })

  it('downloadTemplate 解析 filename*=UTF-8\'\'', async () => {
    mockGet.mockResolvedValueOnce({
      data: new Blob(['x']),
      headers: { 'content-disposition': "attachment; filename*=UTF-8''%E5%B8%AE%E6%89%B6%E6%9D%91.xlsx" },
    })
    let capturedDownload = ''
    const realAnchor = document.createElement('a')
    Object.defineProperty(realAnchor, 'download', {
      get() { return capturedDownload },
      set(v) { capturedDownload = v },
      configurable: true,
    })
    realAnchor.click = vi.fn()
    const realCreate = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: any) => {
      if (tag === 'a') return realAnchor
      return realCreate(tag)
    })
    await downloadTemplate('village')
    expect(capturedDownload).toMatch(/帮扶村/)
  })

  it('getStaticTemplateModules 返回 12 个模板', () => {
    const list = getStaticTemplateModules()
    expect(list).toHaveLength(12)
    expect(list[0].module).toBe('village')
  })

  it('getTemplateInfoByModule 找到匹配', () => {
    const info = getTemplateInfoByModule('population')
    expect(info?.name).toBe('人口数据')
  })

  it('getTemplateInfoByModule 未找到', () => {
    expect(getTemplateInfoByModule('xxx')).toBeUndefined()
  })
})
