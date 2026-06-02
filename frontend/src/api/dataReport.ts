/**
 * Data Report API
 * 数据上报管理API
 */
import request from "./request";
import type {
  DataReport,
  DataReportCreate,
  DataReportReview,
  DataReportStatistics,
  SubordinateReportDashboard,
  DataReportListResponse,
} from "@/types/organization";

const BASE_URL = "/data-reports";

/**
 * 获取数据上报列表
 * @param direction - 'received' 收到的上报, 'submitted' 提交的上报
 */
export async function getDataReports(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  direction?: "received" | "submitted";
}): Promise<DataReportListResponse> {
  const response = await request.get(BASE_URL, { params });
  return response.data;
}

/**
 * 获取上报统计
 */
export async function getReportStatistics(): Promise<DataReportStatistics> {
  const response = await request.get(`${BASE_URL}/statistics`);
  return response.data;
}

/**
 * 获取下级单位上报仪表板
 */
export async function getSubordinateDashboard(): Promise<SubordinateReportDashboard> {
  const response = await request.get(`${BASE_URL}/dashboard`);
  return response.data;
}

/**
 * 获取待审批的上报
 */
export async function getPendingReports(params?: {
  page?: number;
  page_size?: number;
}): Promise<DataReportListResponse> {
  const response = await request.get(`${BASE_URL}/pending`, { params });
  return response.data;
}

/**
 * 获取上报详情
 */
export async function getDataReport(id: number): Promise<DataReport> {
  const response = await request.get(`${BASE_URL}/${id}`);
  return response.data;
}

/**
 * 创建上报
 */
export async function createDataReport(
  data: DataReportCreate,
): Promise<DataReport> {
  const response = await request.post(BASE_URL, data);
  return response.data;
}

/**
 * 提交上报
 */
export async function submitReport(
  id: number,
  comment?: string,
): Promise<DataReport> {
  const response = await request.post(`${BASE_URL}/${id}/submit`, null, {
    params: comment ? { comment } : undefined,
  });
  return response.data;
}

/**
 * 审批上报
 */
export async function reviewReport(
  id: number,
  review: DataReportReview,
): Promise<DataReport> {
  const response = await request.post(`${BASE_URL}/${id}/review`, review);
  return response.data;
}

/**
 * 取消上报
 */
export async function cancelReport(
  id: number,
  reason?: string,
): Promise<DataReport> {
  const response = await request.post(`${BASE_URL}/${id}/cancel`, null, {
    params: reason ? { reason } : undefined,
  });
  return response.data;
}

/**
 * 重新提交上报
 */
export async function resubmitReport(
  id: number,
  comment?: string,
): Promise<DataReport> {
  const response = await request.post(`${BASE_URL}/${id}/resubmit`, null, {
    params: comment ? { comment } : undefined,
  });
  return response.data;
}

/**
 * 获取上报关联的数据包信息
 */
export async function getReportPackage(id: number): Promise<{
  report_id: number;
  package_id: number;
}> {
  const response = await request.get(`${BASE_URL}/${id}/package`);
  return response.data;
}

/**
 * 预览上报数据
 */
export async function previewReportData(id: number): Promise<any[]> {
  const response = await request.get(`${BASE_URL}/${id}/preview`);
  return response.data;
}

/**
 * 下载上报数据包
 */
export async function downloadReportPackage(id: number): Promise<Blob> {
  const response = await request.get(`${BASE_URL}/${id}/download`, {
    responseType: "blob",
  });
  return response.data;
}
