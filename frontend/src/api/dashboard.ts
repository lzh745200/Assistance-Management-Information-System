/**
 * 仪表盘API服务
 * 提供首页统计数据、近期动态的增删改查
 */

import { get, post, put, del, apiRequest } from '@/api/request'

const BASE_URL = '/dashboard'

/** 获取仪表盘统计数据 */
export function getDashboardStats(refresh?: boolean): Promise<any> {
  return apiRequest({
    method: 'GET',
    url: `${BASE_URL}/stats`,
    params: { refresh: refresh ?? false },
  })
}

/** 仪表盘汇总（统计 + 近期动态，一次请求） */
export function getDashboardSummary(): Promise<any> {
  return get(`${BASE_URL}/summary`)
}

/** 获取近期动态 */
export function getRecentActivities(): Promise<any> {
  return get(`${BASE_URL}/recent-activities`)
}

/** 创建自定义动态 */
export function createActivity(data: {
  type?: string
  action: string
  target: string
}): Promise<any> {
  return post(`${BASE_URL}/recent-activities`, data)
}

/** 更新自定义动态 */
export function updateActivity(
  activityId: string,
  data: {
    type?: string
    action?: string
    target?: string
  }
): Promise<any> {
  return put(`${BASE_URL}/recent-activities/${activityId}`, data)
}

/** 删除动态（自定义动态物理删除，系统动态持久化隐藏） */
export function deleteActivity(activityId: string): Promise<any> {
  return del(`${BASE_URL}/recent-activities/${activityId}`)
}

/** KPI 年度同比趋势 */
export function getKpiTrends(): Promise<any> {
  return get(`${BASE_URL}/kpi-trends`)
}

/** 年度趋势对比数据 */
export function getYearlyTrends(years?: number): Promise<any> {
  return get(`${BASE_URL}/yearly-trends`, { params: { years: years ?? 5 } })
}
