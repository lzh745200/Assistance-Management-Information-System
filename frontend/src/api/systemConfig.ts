/**
 * 系统配置 API
 * 提供系统运行参数的查询和修改功能
 */

import { get, put, del, post } from "./request";

// ==================== 类型定义 ====================

/** 配置项 */
export interface ConfigItem {
  key: string;
  value: string;
  description?: string;
}

/** 配置列表响应 */
export interface ConfigListResponse {
  items: ConfigItem[];
  total: number;
}

/** 配置详情 */
export interface ConfigDetail {
  key: string;
  value: string;
  description: string;
}

/** 默认配置项 */
export interface DefaultConfigItem {
  key: string;
  value: string;
  description: string;
}

/** 默认配置列表 */
export interface DefaultConfigList {
  defaults: DefaultConfigItem[];
  total: number;
}

/** 配置导出 */
export interface ConfigExport {
  format: string;
  content: string;
}

// ==================== 工具函数 ====================

/** 构建查询字符串 */
function buildQuery(params: Record<string, string | undefined>): string {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== undefined)
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`);
  return parts.length > 0 ? `?${parts.join("&")}` : "";
}

// ==================== API 函数 ====================

/** 获取所有系统配置 */
export async function listSystemConfig(): Promise<{
  success: boolean;
  data: ConfigListResponse;
}> {
  return get("/config");
}

/** 获取指定配置项 */
export async function getSystemConfig(
  key: string,
): Promise<{ success: boolean; data: ConfigDetail }> {
  return get(`/config/${key}`);
}

/** 更新指定配置项（value 和 description 为查询参数） */
export async function updateSystemConfig(
  key: string,
  value: string,
  description?: string,
): Promise<{
  success: boolean;
  message: string;
  data: { key: string; value: string };
}> {
  const qs = buildQuery({ value, description });
  return put(`/config/${key}${qs}`);
}

/** 批量更新配置项 */
export async function batchUpdateSystemConfig(configs: ConfigItem[]): Promise<{
  success: boolean;
  message: string;
  data: { updated_keys: string[] };
}> {
  return put("/config", { configs });
}

/** 删除指定配置项 */
export async function deleteSystemConfig(
  key: string,
): Promise<{ success: boolean; message: string }> {
  return del(`/config/${key}`);
}

/** 导出配置为 JSON */
export async function exportSystemConfig(): Promise<{
  success: boolean;
  data: ConfigExport;
}> {
  return get("/config/export/json");
}

/** 从 JSON 导入配置 */
export async function importSystemConfig(
  data: string,
): Promise<{ success: boolean; message: string }> {
  return post("/config/import/json", { data });
}

/** 获取默认配置值 */
export async function getDefaultConfigs(): Promise<{
  success: boolean;
  data: DefaultConfigList;
}> {
  return get("/config/defaults");
}

// ==================== 分组导出 ====================

export const systemConfigApi = {
  listConfig: listSystemConfig,
  getConfig: getSystemConfig,
  updateConfig: updateSystemConfig,
  batchUpdateConfig: batchUpdateSystemConfig,
  deleteConfig: deleteSystemConfig,
  exportConfig: exportSystemConfig,
  importConfig: importSystemConfig,
  getDefaults: getDefaultConfigs,
};
