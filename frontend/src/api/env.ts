/**
 * 运行环境检查 API
 * 提供系统运行环境的诊断与检查
 */

import { get } from '@/api/request'

// ==================== 类型定义 ====================

/** 系统信息 */
export interface SystemInfo {
  python_version: string
  platform: string
  env_mode: string
}

/** 环境检查结果 */
export interface EnvCheckResult {
  system: SystemInfo
  packages: Record<string, string>
  missing_packages: string[]
  fix_command?: string
}

// ==================== API 函数 ====================

/** 检查系统运行环境 */
export async function checkEnv(): Promise<EnvCheckResult> {
  return get<EnvCheckResult>('/env/check')
}

// ==================== 分组导出 ====================

export const envApi = {
  check: checkEnv,
}
