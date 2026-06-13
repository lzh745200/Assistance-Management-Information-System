/**
 * 数据分析API服务
 * Feature: data-analytics-enhancement
 * Requirements: 1.2, 2.1-2.5
 */

import { get, post, apiRequest } from "./request";
import type {
  VillageFilters,
  FilterOptions,
  DrillDownQuery,
  DrillDownResult,
  SummaryStatistics,
  VillageCompareResult,
  YearCompareResult,
  CompareMetric,
  SupportedVillage,
} from "@/types/analytics";

const BASE_URL = "/reports/analytics";

// ==================== 筛选查询 ====================

/**
 * 获取筛选选项
 */
export async function getFilterOptions(): Promise<FilterOptions> {
  const response = await get<FilterOptions>(`${BASE_URL}/filter-options`);
  return response;
}

/**
 * 多维度筛选帮扶村
 */
export async function filterVillages(
  filters: VillageFilters,
  page = 1,
  pageSize = 20,
): Promise<{
  total: number;
  page: number;
  pageSize: number;
  pages: number;
  items: SupportedVillage[];
}> {
  const response = await apiRequest<{
    total: number;
    page: number;
    page_size: number;
    pages: number;
    items: SupportedVillage[];
  }>({
    method: "POST",
    url: `${BASE_URL}/filter`,
    data: filters,
    params: { page, page_size: pageSize },
  });

  return {
    total: response.total,
    page: response.page,
    pageSize: response.page_size,
    pages: response.pages,
    items: response.items,
  };
}

// ==================== 数据钻取 ====================

/**
 * 数据钻取查询
 */
export async function drillDown(
  query: DrillDownQuery,
): Promise<DrillDownResult> {
  const response = await post<DrillDownResult>(`${BASE_URL}/drill-down`, {
    dimension: query.dimension,
    value: query.value,
    target_dimension: query.targetDimension,
    filters: query.filters,
  });
  return response;
}

// ==================== 对比分析 ====================

/**
 * 对比多个帮扶村的数据
 */
export async function compareVillages(
  villageIds: number[],
  year: number,
  metrics?: CompareMetric[],
): Promise<VillageCompareResult> {
  const response = await apiRequest<VillageCompareResult>({
    method: "POST",
    url: `${BASE_URL}/compare-villages`,
    data: villageIds,
    params: {
      year,
      metrics: metrics?.join(","),
    },
  });
  return response;
}

/**
 * 对比同一帮扶村不同年份的数据
 */
export async function compareYears(
  villageId: number,
  years: number[],
  metrics?: CompareMetric[],
): Promise<YearCompareResult> {
  const response = await get<YearCompareResult>(
    `${BASE_URL}/compare-years/${villageId}`,
    {
      params: {
        years: years.join(","),
        metrics: metrics?.join(","),
      },
    },
  );
  return response;
}

// ==================== 统计汇总 ====================

/**
 * 获取汇总统计数据
 */
export async function getSummaryStatistics(params?: {
  year?: number;
  department?: string;
  isThreeRegions?: boolean;
  isKeyCounty?: boolean;
}): Promise<SummaryStatistics> {
  const response = await get<SummaryStatistics>(`${BASE_URL}/summary`, {
    params: {
      year: params?.year,
      department: params?.department,
      is_three_regions: params?.isThreeRegions,
      is_key_county: params?.isKeyCounty,
    },
  });
  return response;
}

// ==================== 数据分析核心端点 (/analytics/*) ====================

const ANALYTICS_BASE = "/analytics";

/** 获取仪表盘数据 */
export async function getDashboard(dateRange?: string, filters?: string): Promise<any> {
  return get(`${ANALYTICS_BASE}/dashboard`, { date_range: dateRange, filters });
}

/** 获取帮扶村分析数据 */
export async function getVillageAnalysis(): Promise<any> {
  return get(`${ANALYTICS_BASE}/village-analysis`);
}

/** 获取资金趋势分析 */
export async function getFundingTrends(years?: number): Promise<any> {
  return get(`${ANALYTICS_BASE}/funding-trends`, { years: years ?? 5 });
}

/** 获取绩效指标数据 */
export async function getPerformanceMetrics(): Promise<any> {
  return get(`${ANALYTICS_BASE}/performance-metrics`);
}

/** 获取对比分析数据 */
export async function getComparisonAnalysis(data: {
  province?: string;
  compare_type?: string;
  target_value?: string;
}): Promise<any> {
  return post(`${ANALYTICS_BASE}/comparison`, data);
}

/** 生成数据分析报表 */
export async function generateReport(data: {
  report_type?: string;
  start_date?: string;
  end_date?: string;
}): Promise<any> {
  return post(`${ANALYTICS_BASE}/generate-report`, data);
}

/** 导出分析数据 */
export async function exportData(data: {
  report_type?: string;
  start_date?: string;
  end_date?: string;
}): Promise<any> {
  return post(`${ANALYTICS_BASE}/export`, data);
}

/** 获取实时统计数据 */
export async function getRealtimeStats(): Promise<any> {
  return get(`${ANALYTICS_BASE}/realtime-stats`);
}

/** 获取KPI汇总数据 */
export async function getKpiSummary(period?: string): Promise<any> {
  return get(`${ANALYTICS_BASE}/kpi-summary`, { period: period ?? "month" });
}

/** 获取分析服务健康状态 */
export async function getAnalyticsHealth(): Promise<any> {
  return get(`${ANALYTICS_BASE}/health`);
}
