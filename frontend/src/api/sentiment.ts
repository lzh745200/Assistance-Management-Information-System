/**
 * 舆情监控API服务
 * 提供舆情数据采集、分析、统计和预警功能
 */

import api from './request'

const BASE_URL = '/sentiment'

/** 采集新闻（需要管理员权限） */
export function collectNews(data: { keywords: string[] }): Promise<any> {
  return api.post(`${BASE_URL}/collect`, data)
}

/** 批量分析新闻情感（需要管理员权限） */
export function analyzeNews(limit?: number): Promise<any> {
  return api.post(`${BASE_URL}/analyze`, null, {
    params: { limit: limit ?? 100 },
  })
}

/** 获取新闻列表 */
export function getNews(params?: {
  sentiment_label?: string
  is_alert?: boolean
  days?: number
  limit?: number
  offset?: number
}): Promise<any> {
  return api.get(`${BASE_URL}/news`, { params })
}

/** 获取舆情统计 */
export function getStatistics(days?: number): Promise<any> {
  return api.get(`${BASE_URL}/statistics`, {
    params: { days: days ?? 7 },
  })
}

/** 获取热词列表 */
export function getHotKeywords(days?: number, topK?: number): Promise<any> {
  return api.get(`${BASE_URL}/hot-keywords`, {
    params: { days: days ?? 7, top_k: topK ?? 20 },
  })
}

/** 获取预警列表 */
export function getAlerts(days?: number, limit?: number): Promise<any> {
  return api.get(`${BASE_URL}/alerts`, {
    params: { days: days ?? 7, limit: limit ?? 50 },
  })
}
