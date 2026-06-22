/**
 * 成效评估API服务
 * 提供村庄成效评估、报告查询、对比和排名功能
 */

import api from './request'

const BASE_URL = '/effectiveness'

/** 评估村庄成效（需要管理员权限） */
export function evaluateVillage(data: { village_id: number; year: number }): Promise<any> {
  return api.post(`${BASE_URL}/evaluate`, data)
}

/** 获取评估报告 */
export function getEvaluationReport(villageId: number, year: number): Promise<any> {
  return api.get(`${BASE_URL}/report/${villageId}`, {
    params: { year },
  })
}

/** 对比两年的评估结果 */
export function compareEvaluations(villageId: number, year1: number, year2: number): Promise<any> {
  return api.get(`${BASE_URL}/compare/${villageId}`, {
    params: { year1, year2 },
  })
}

/** 获取排名列表 */
export function getRankings(year: number, limit?: number): Promise<any> {
  return api.get(`${BASE_URL}/rankings`, {
    params: { year, limit: limit ?? 20 },
  })
}
