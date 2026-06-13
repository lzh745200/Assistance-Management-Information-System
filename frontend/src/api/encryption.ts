/**
 * 数据库加密管理 API
 * 提供数据库加密的初始化、密码修改、状态查询和禁用功能
 */

import { get, post } from "./request";

// ==================== 类型定义 ====================

/** 加密状态 */
export interface EncryptionStatus {
  is_enabled: boolean;
  has_salt: boolean;
  iterations: number;
}

// ==================== API 函数 ====================

/** 初始化数据库加密 */
export async function initializeEncryption(data: {
  password: string;
  confirm_password: string;
}): Promise<{ success: boolean; message: string }> {
  return post("/encryption/initialize", data);
}

/** 修改加密密码 */
export async function changeEncryptionPassword(data: {
  old_password: string;
  new_password: string;
  confirm_password: string;
}): Promise<{ success: boolean; message: string }> {
  return post("/encryption/change-password", data);
}

/** 获取加密状态 */
export async function getEncryptionStatus(): Promise<{
  success: boolean;
  data: EncryptionStatus;
}> {
  return get("/encryption/status");
}

/** 禁用数据库加密 */
export async function disableEncryption(data: {
  password: string;
}): Promise<{ success: boolean; message: string }> {
  return post("/encryption/disable", data);
}

// ==================== 分组导出 ====================

export const encryptionApi = {
  initialize: initializeEncryption,
  changePassword: changeEncryptionPassword,
  getStatus: getEncryptionStatus,
  disable: disableEncryption,
};
