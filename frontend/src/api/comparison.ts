/**
 * 对比图片API
 * 提供对比图片相关的接口调用
 */
import request from "./request";

export interface ComparisonImage {
  id?: number;
  type: string;
  reference_id: number;
  title: string;
  description?: string;
  before_image: string;
  after_image: string;
  before_date?: string;
  after_date?: string;
  photographer?: string;
  location?: string;
  tags?: string;
  category?: string;
  display_order?: number;
  is_featured?: number;
  view_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface ComparisonImageQuery {
  type?: string;
  reference_id?: number;
  category?: string;
  is_featured?: number;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface ComparisonImageList {
  total: number;
  items: ComparisonImage[];
  page: number;
  page_size: number;
}

/**
 * 获取对比图片列表
 */
export function getComparisonList(
  params: ComparisonImageQuery,
): Promise<ComparisonImageList> {
  return request({
    url: "/comparisons",
    method: "get",
    params,
  });
}

/**
 * 获取对比图片详情
 */
export function getComparisonDetail(id: number): Promise<ComparisonImage> {
  return request({
    url: `/comparisons/${id}`,
    method: "get",
  });
}

/**
 * 创建对比图片
 */
export function createComparison(
  data: ComparisonImage,
): Promise<ComparisonImage> {
  return request({
    url: "/comparisons",
    method: "post",
    data,
  });
}

/**
 * 上传对比图片
 */
export function uploadComparisonImages(
  formData: FormData,
): Promise<ComparisonImage> {
  return request({
    url: "/comparisons/upload",
    method: "post",
    data: formData,
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

/**
 * 更新对比图片
 */
export function updateComparison(
  id: number,
  data: Partial<ComparisonImage>,
): Promise<ComparisonImage> {
  return request({
    url: `/comparisons/${id}`,
    method: "put",
    data,
  });
}

/**
 * 删除对比图片
 */
export function deleteComparison(id: number): Promise<void> {
  return request({
    url: `/comparisons/${id}`,
    method: "delete",
  });
}

/**
 * 获取精选对比图片
 */
export function getFeaturedComparisons(
  type?: string,
  limit: number = 10,
): Promise<ComparisonImage[]> {
  return request({
    url: "/comparisons/featured/list",
    method: "get",
    params: { type, limit },
  });
}

/**
 * 获取对比图片统计
 */
export function getComparisonStatistics(
  type: string,
  referenceId: number,
): Promise<any> {
  return request({
    url: `/comparisons/statistics/${type}/${referenceId}`,
    method: "get",
  });
}

/**
 * 批量更新显示顺序
 */
export function batchUpdateOrder(
  orderData: Array<{ id: number; order: number }>,
): Promise<any> {
  return request({
    url: "/comparisons/batch/order",
    method: "post",
    data: orderData,
  });
}

export default {
  getComparisonList,
  getComparisonDetail,
  createComparison,
  uploadComparisonImages,
  updateComparison,
  deleteComparison,
  getFeaturedComparisons,
  getComparisonStatistics,
  batchUpdateOrder,
};
