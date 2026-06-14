/**
 * 数据包加密导入导出API
 */

import request from "./request";

// 类型定义
export interface DataPackageExportEncryptedRequest {
  data_types: string[];
  password?: string;
  description?: string;
}

export interface DataPackageExportResult {
  package_id: number;
  package_code: string;
  file_path: string;
  file_name: string;
  file_size: number;
  download_url: string;
}

export interface EncryptionInfo {
  enabled: boolean;
  algorithm?: string;
  salt?: string;
  iterations?: number;
}

export interface ConflictInfo {
  data_type: string;
  business_key: Record<string, any>;
  differences: string[];
  local_data: Record<string, any>;
  import_data: Record<string, any>;
}

export interface ImportPreviewResult {
  package_id: number;
  is_encrypted: boolean;
  manifest: Record<string, any>;
  new_records_count: number;
  conflict_records_count: number;
  conflicts: ConflictInfo[];
}

export interface ImportConfirmRequest {
  package_id: number;
  conflict_strategy: "SKIP" | "OVERWRITE" | "KEEP_BOTH" | "MERGE";
}

export interface ImportConfirmResult {
  success: boolean;
  imported_counts: Record<string, number>;
  id_mapping: Record<string, Record<number, number>>;
  message: string;
}

export interface DataPackageResponse {
  id: number;
  package_code: string;
  org_id: number;
  file_name: string;
  file_size: number;
  status: string;
  is_encrypted: boolean;
  created_at: string;
}

// API函数

/**
 * 导出加密数据包
 */
export function exportEncryptedPackage(
  data: DataPackageExportEncryptedRequest,
): Promise<DataPackageExportResult> {
  return request.post("/data-packages/export-encrypted", data);
}

/**
 * 上传加密数据包（第一步）
 */
export function uploadEncryptedPackage(
  file: File,
  password?: string,
): Promise<DataPackageResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (password) {
    formData.append("password", password);
  }

  return request.post("/data-packages/upload-encrypted", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

/**
 * 解密并预览数据包（第二步）
 */
export function decryptAndPreview(
  packageId: number,
  password: string,
): Promise<ImportPreviewResult> {
  return request.post(`/data-packages/decrypt-preview/${packageId}`, null, {
    params: { password },
  });
}

/**
 * 确认导入并处理冲突（第三步）
 */
export function confirmImport(
  data: ImportConfirmRequest,
): Promise<ImportConfirmResult> {
  return request.post(`/data-packages/confirm-import/${data.package_id}`, {
    conflict_strategy: data.conflict_strategy,
  });
}

/**
 * 下载数据包
 */
export function downloadPackage(packageId: number): string {
  const base = import.meta.env.VITE_API_BASE_URL || "/api/v1";
  const apiBase = base.endsWith("/api/v1")
    ? base
    : `${base.replace(/\/$/, "")}/api/v1`;
  return `${apiBase}/data-packages/${packageId}/download`;
}
