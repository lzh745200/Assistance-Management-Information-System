import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
}))

import {
  getLanguages,
  getTranslations,
  translateKey,
  getMissingKeys,
  getCurrentLanguage,
  i18nApi,
} from '@/api/i18n'

describe('api/i18n', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getLanguages GET /system/i18n/languages', async () => {
    const body = { success: true, data: [] }
    mockGet.mockResolvedValueOnce(body)
    const r = await getLanguages()
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/languages')
    expect(r).toBe(body)
  })

  it('getTranslations 不带 namespace', async () => {
    const body = { success: true, data: { language: 'en' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getTranslations('en')
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/translations/en', undefined)
    expect(r).toBe(body)
  })

  it('getTranslations 带 namespace', async () => {
    const body = { success: true, data: { language: 'en' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getTranslations('en', 'common')
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/translations/en', {
      namespace: 'common',
    })
    expect(r).toBe(body)
  })

  it('translateKey 默认语言 zh-CN', async () => {
    const body = { success: true, data: { key: 'hello', value: '你好' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await translateKey('hello')
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/translate', {
      key: 'hello',
      language: 'zh-CN',
    })
    expect(r).toBe(body)
  })

  it('translateKey 指定语言', async () => {
    mockGet.mockResolvedValueOnce({ success: true })
    await translateKey('hello', 'en')
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/translate', {
      key: 'hello',
      language: 'en',
    })
  })

  it('getMissingKeys 默认参数', async () => {
    const body = { success: true, data: { missing_count: 0 } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getMissingKeys()
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/missing-keys', {
      source_lang: 'zh-CN',
      target_lang: 'en',
    })
    expect(r).toBe(body)
  })

  it('getMissingKeys 自定义语言对', async () => {
    mockGet.mockResolvedValueOnce({ success: true })
    await getMissingKeys('en', 'fr')
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/missing-keys', {
      source_lang: 'en',
      target_lang: 'fr',
    })
  })

  it('getCurrentLanguage GET /system/i18n/current', async () => {
    const body = { success: true, data: { language: 'zh-CN', name: '简体中文' } }
    mockGet.mockResolvedValueOnce(body)
    const r = await getCurrentLanguage()
    expect(mockGet).toHaveBeenCalledWith('/system/i18n/current')
    expect(r).toBe(body)
  })

  it('i18nApi 分组导出引用同一批函数', () => {
    expect(i18nApi.getLanguages).toBe(getLanguages)
    expect(i18nApi.getTranslations).toBe(getTranslations)
    expect(i18nApi.translate).toBe(translateKey)
    expect(i18nApi.getMissingKeys).toBe(getMissingKeys)
    expect(i18nApi.getCurrentLanguage).toBe(getCurrentLanguage)
  })
})
