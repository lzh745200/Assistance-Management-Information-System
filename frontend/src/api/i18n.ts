/**
 * 国际化 API
 * 提供系统多语言支持和翻译资源管理
 */

import { get } from './request'

// ==================== 类型定义 ====================

/** 支持的语言 */
export interface Language {
  code: string
  name: string
  flag: string
  default: boolean
}

/** 翻译资源 */
export interface TranslationResource {
  language: string
  translations: Record<string, string>
  total_keys: number
}

/** 单键翻译结果 */
export interface TranslateResult {
  key: string
  language: string
  value: string
  fallback: boolean
}

/** 缺失翻译键报告 */
export interface MissingKeysReport {
  source_language: string
  target_language: string
  source_count: number
  target_count: number
  missing_keys: string[]
  missing_count: number
  extra_keys: string[]
  completion_rate: number
}

/** 当前语言设置 */
export interface CurrentLanguage {
  language: string
  name: string
}

// ==================== API 函数 ====================

/** 获取支持的语言列表 */
export async function getLanguages(): Promise<{
  success: boolean
  data: Language[]
}> {
  return get('/i18n/languages')
}

/** 获取指定语言的翻译资源 */
export async function getTranslations(
  lang: string,
  namespace?: string
): Promise<{ success: boolean; data: TranslationResource }> {
  return get(`/i18n/translations/${lang}`, namespace ? { namespace } : undefined)
}

/** 翻译单个键值 */
export async function translateKey(
  key: string,
  language?: string
): Promise<{ success: boolean; data: TranslateResult }> {
  return get('/i18n/translate', { key, language: language || 'zh-CN' })
}

/** 检查缺失的翻译键 */
export async function getMissingKeys(
  sourceLang?: string,
  targetLang?: string
): Promise<{ success: boolean; data: MissingKeysReport }> {
  return get('/i18n/missing-keys', {
    source_lang: sourceLang || 'zh-CN',
    target_lang: targetLang || 'en',
  })
}

/** 获取当前用户语言偏好 */
export async function getCurrentLanguage(): Promise<{
  success: boolean
  data: CurrentLanguage
}> {
  return get('/i18n/current')
}

// ==================== 分组导出 ====================

export const i18nApi = {
  getLanguages,
  getTranslations,
  translate: translateKey,
  getMissingKeys,
  getCurrentLanguage,
}
