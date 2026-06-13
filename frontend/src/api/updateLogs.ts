/**
 * 系统更新日志 API
 * 提供系统版本更新历史的查询、记录和管理功能
 */

import { get, post, del } from "./request";

// ==================== 类型定义 ====================

/** 更新日志 */
export interface UpdateLog {
  id: string;
  version: string;
  description: string;
  updated_by?: string;
  created_at: string;
}

/** 更新日志列表响应 */
export interface UpdateLogListResponse {
  items: UpdateLog[];
  total: number;
  page: number;
  page_size: number;
}

/** 最新版本信息 */
export interface LatestVersionInfo {
  version: string;
  message?: string;
  has_records?: boolean;
}

/** 版本初始化参数 */
export interface VersionInitParams {
  updated_by?: string;
  force?: boolean;
}

/** 版本检查结果 */
export interface VersionCheckResult {
  current_version: string;
  message?: string;
  check_error?: string;
}

// ==================== API 函数 ====================

/** 获取更新日志列表 */
export async function listUpdateLogs(params?: {
  page?: number;
  page_size?: number;
  version?: string;
}): Promise<{ success: boolean; data: UpdateLogListResponse }> {
  return get("/update-logs", params);
}

/** 获取最新更新日志 */
export async function getLatestUpdateLog(): Promise<{
  success: boolean;
  data: UpdateLog | LatestVersionInfo;
}> {
  return get("/update-logs/latest");
}

/** 获取更新日志详情 */
export async function getUpdateLog(
  updateId: string,
): Promise<{ success: boolean; data: UpdateLog }> {
  return get(`/update-logs/${updateId}`);
}

/** 创建更新日志 */
export async function createUpdateLog(data: {
  version: string;
  description: string;
  updated_by?: string;
}): Promise<{
  success: boolean;
  message: string;
  data: UpdateLog;
}> {
  return post("/update-logs", data);
}

/** 初始化版本历史 */
export async function initializeVersionHistory(
  params?: VersionInitParams,
): Promise<{
  success: boolean;
  message: string;
  data: Record<string, any>;
}> {
  return post("/update-logs/initialize", params || {});
}

/** 同步版本历史 */
export async function syncVersionHistory(): Promise<{
  success: boolean;
  message: string;
  data: Record<string, any>;
}> {
  return post("/update-logs/sync");
}

/** 删除更新日志 */
export async function deleteUpdateLog(
  updateId: string,
): Promise<{ success: boolean; message: string }> {
  return del(`/update-logs/${updateId}`);
}

/** 检查版本变更 */
export async function checkVersionChange(): Promise<{
  success: boolean;
  message: string;
  data: VersionCheckResult | Record<string, any>;
}> {
  return get("/update-logs/check/version");
}

// ==================== 分组导出 ====================

export const updateLogsApi = {
  listLogs: listUpdateLogs,
  getLatest: getLatestUpdateLog,
  getLog: getUpdateLog,
  createLog: createUpdateLog,
  initialize: initializeVersionHistory,
  sync: syncVersionHistory,
  deleteLog: deleteUpdateLog,
  checkVersion: checkVersionChange,
};
