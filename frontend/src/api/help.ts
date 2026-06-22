/**
 * 帮助中心 API
 * 提供系统使用帮助、用户手册、常见问题解答等功能
 */

import { get } from './request'

// ==================== 类型定义 ====================

/** 帮助分类 */
export interface HelpCategory {
  key: string
  name: string
  count: number
}

/** 帮助分类列表 */
export interface HelpCategoryList {
  categories: HelpCategory[]
}

/** 帮助文档摘要 */
export interface HelpArticleSummary {
  id: number
  category: string
  title: string
  summary: string
  tags: string[]
}

/** 帮助文档详情 */
export interface HelpArticle {
  id: number
  category: string
  title: string
  content: string
  tags: string[]
}

/** 帮助文档列表响应 */
export interface HelpArticleListResponse {
  items: HelpArticleSummary[]
  total: number
  page: number
  page_size: number
}

/** 搜索结果项 */
export interface HelpSearchResult {
  id: number
  category: string
  title: string
  snippet: string
  tags: string[]
  relevance_score: number
}

/** 搜索结果响应 */
export interface HelpSearchResponse {
  items: HelpSearchResult[]
  total: number
}

/** 系统信息 */
export interface SystemInfo {
  name: string
  short_name: string
  version: string
  description: string
  features: string[]
  contact: {
    technical_support: string
    feedback: string
  }
}

// ==================== API 函数 ====================

/** 获取帮助分类列表 */
export async function getHelpCategories(): Promise<{
  success: boolean
  data: HelpCategoryList
}> {
  return get('/help/categories')
}

/** 获取帮助文档列表 */
export async function getHelpArticles(params?: {
  category?: string
  keyword?: string
  page?: number
  page_size?: number
}): Promise<{ success: boolean; data: HelpArticleListResponse }> {
  return get('/help/articles', params)
}

/** 获取帮助文档详情 */
export async function getHelpArticle(
  articleId: number
): Promise<{ success: boolean; data: HelpArticle }> {
  return get(`/help/articles/${articleId}`)
}

/** 搜索帮助文档 */
export async function searchHelp(
  q: string,
  limit?: number
): Promise<{ success: boolean; data: HelpSearchResponse }> {
  return get('/help/search', { q, limit: limit || 10 })
}

/** 获取系统简介 */
export async function getHelpSystemInfo(): Promise<{
  success: boolean
  data: SystemInfo
}> {
  return get('/help/system-info')
}

// ==================== 分组导出 ====================

export const helpApi = {
  getCategories: getHelpCategories,
  getArticles: getHelpArticles,
  getArticle: getHelpArticle,
  search: searchHelp,
  getSystemInfo: getHelpSystemInfo,
}
