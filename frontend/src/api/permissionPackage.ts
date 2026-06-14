/**
 * 权限配置包 API 客户端
 *
 * 用于离线多机协作场景下的权限同步。
 * 提供导出/导入/预览/确认/下载功能。
 */
import request from "./request";

/**
 * 导出权限配置包
 * @param password 可选的加密密码
 */
export async function exportPermissionPackage(password?: string) {
  return request.post("/permission-packages/export", {
    password: password || undefined,
  });
}

/**
 * 导入权限配置包（验证 + 预览阶段）
 * @param file ZIP 文件
 */
export async function importPermissionPackage(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return request.post("/permission-packages/import", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

/**
 * 获取导入预览详情
 * @param fileName 上传的文件名
 */
export async function previewPermissionPackage(fileName: string) {
  return request.get(`/permission-packages/preview/${fileName}`);
}

/**
 * 确认导入权限配置包
 * @param fileName 上传的文件名
 * @param overwrite 是否覆盖已有配置
 */
export async function confirmPermissionPackage(
  fileName: string,
  overwrite: boolean = true,
) {
  return request.post(`/permission-packages/confirm/${fileName}`, {
    overwrite_existing: overwrite,
  });
}

/**
 * 下载权限配置包
 * @param fileName 文件名
 */
export function getPermissionPackageDownloadUrl(fileName: string): string {
  return `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}/permission-packages/download/${fileName}`;
}
