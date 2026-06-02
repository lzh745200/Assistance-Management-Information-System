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
