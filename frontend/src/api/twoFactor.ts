/**
 * 双因素认证 API
 * 提供 TOTP 双因素认证的启用、验证、禁用和状态查询
 */

import { get, post } from '@/api/request'

// ==================== 类型定义 ====================

/** 启用双因素认证响应 */
export interface EnableTwoFactorResponse {
  secret: string
  qr_code: string
  backup_codes: string[]
}

/** 双因素认证状态 */
export interface TwoFactorStatus {
  enabled: boolean
}

// ==================== API 函数 ====================

/** 启用双因素认证（返回密钥、二维码和备用码） */
export async function enableTwoFactor(): Promise<EnableTwoFactorResponse> {
  return post<EnableTwoFactorResponse>('/two-factor/enable')
}

/** 验证 TOTP 令牌并正式启用双因素认证 */
export async function verifyAndEnableTwoFactor(token: string): Promise<{ message: string }> {
  return post<{ message: string }>('/two-factor/verify', { token })
}

/** 禁用双因素认证 */
export async function disableTwoFactor(): Promise<{ message: string }> {
  return post<{ message: string }>('/two-factor/disable')
}

/** 获取双因素认证状态 */
export async function getTwoFactorStatus(): Promise<TwoFactorStatus> {
  return get<TwoFactorStatus>('/two-factor/status')
}

// ==================== 分组导出 ====================

export const twoFactorApi = {
  enable: enableTwoFactor,
  verifyAndEnable: verifyAndEnableTwoFactor,
  disable: disableTwoFactor,
  getStatus: getTwoFactorStatus,
}
