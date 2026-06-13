/**
 * 报表模板管理API服务
 * 上级可创建模板并分配给下级；下级下载模板、填写、上传
 */

import api from "./request";

const BASE_URL = "/report-templates";

/** 获取报表模板列表 */
export function listTemplates(params?: {
  type?: string;
  module?: string;
  is_active?: boolean;
}): Promise<any> {
  return api.get(BASE_URL, { params });
}

/** 创建报表模板 */
export function createTemplate(data: {
  name: string;
  type: string;
  module: string;
  fields?: string;
  format_config?: string;
  description?: string;
}): Promise<any> {
  return api.post(BASE_URL, data);
}

/** 获取模板详情 */
export function getTemplate(id: number): Promise<any> {
  return api.get(`${BASE_URL}/${id}`);
}

/** 更新模板 */
export function updateTemplate(
  id: number,
  data: {
    name?: string;
    type?: string;
    module?: string;
    fields?: string;
    format_config?: string;
    description?: string;
    is_active?: boolean;
  },
): Promise<any> {
  return api.put(`${BASE_URL}/${id}`, data);
}

/** 删除模板 */
export function deleteTemplate(id: number): Promise<any> {
  return api.delete(`${BASE_URL}/${id}`);
}

/** 下载模板 Excel 文件（根据字段映射自动生成） */
export function downloadTemplate(id: number): Promise<any> {
  return api.get(`${BASE_URL}/${id}/download`, {
    responseType: "blob",
  });
}

/** 上传已填写的模板 Excel 文件 */
export function uploadFilledTemplate(
  id: number,
  file: File,
  mode?: string,
  importMode?: string,
): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  return api.post(`${BASE_URL}/${id}/upload`, formData, {
    params: {
      mode: mode ?? "preview",
      import_mode: importMode ?? "incremental",
    },
  });
}
