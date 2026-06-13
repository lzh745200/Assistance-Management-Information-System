/**
 * AI智能分析API服务
 * 提供数据分析、趋势预测、异常检测、智能推荐、自然语言查询等功能
 */

import api from "./request";

// ==================== AI 基础服务 (/ai/*) ====================

const AI_BASE = "/ai";

/** 获取AI服务运行状态 */
export function getStatus(): Promise<any> {
  return api.get(`${AI_BASE}/status`);
}

/** 执行AI数据分析 */
export function analyze(data: {
  analysis_type?: string;
  data?: Record<string, any>;
  description?: string;
}): Promise<any> {
  return api.post(`${AI_BASE}/analyze`, data);
}

/** 获取基于上下文的智能推荐 */
export function getRecommendations(data: {
  context?: Record<string, any>;
  category?: string;
}): Promise<any> {
  return api.post(`${AI_BASE}/recommendations`, data);
}

/** 收入趋势预测 */
export function forecastIncome(forecastYears?: number): Promise<any> {
  return api.get(`${AI_BASE}/forecast/income`, {
    params: { forecast_years: forecastYears ?? 2 },
  });
}

/** 年度经费完成率预测 */
export function forecastFunds(): Promise<any> {
  return api.get(`${AI_BASE}/forecast/funds`);
}

// ==================== AI 增强服务 (/ai-enhanced/*) ====================

const AI_ENHANCED_BASE = "/ai-enhanced";

/** 趋势预测 */
export function predictTrend(data: {
  historical_data: Array<Record<string, any>>;
  periods?: number;
  date_field?: string;
  value_field?: string;
  method?: string;
}): Promise<any> {
  return api.post(`${AI_ENHANCED_BASE}/predict`, data);
}

/** 异常检测 */
export function detectAnomalies(data: {
  data: Array<Record<string, any>>;
  value_field?: string;
  method?: string;
  contamination?: number;
}): Promise<any> {
  return api.post(`${AI_ENHANCED_BASE}/anomaly-detection`, data);
}

/** 项目推荐 */
export function recommendProjects(
  villageId: number,
  limit?: number,
): Promise<any> {
  return api.get(`${AI_ENHANCED_BASE}/recommendations/projects`, {
    params: { village_id: villageId, limit: limit ?? 5 },
  });
}

/** 资金分配建议 */
export function recommendFundAllocation(data: {
  total_budget: number;
  village_ids: number[];
}): Promise<any> {
  return api.post(`${AI_ENHANCED_BASE}/recommendations/fund-allocation`, data);
}

/** 自然语言查询 */
export function nlpQuery(query: string): Promise<any> {
  return api.post(`${AI_ENHANCED_BASE}/nlp-query`, null, {
    params: { query },
  });
}
