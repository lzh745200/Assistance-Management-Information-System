/**
 * 安全等级与安全工具
 *
 * 提供军队安全等级枚举和相关工具函数。
 */

/** 安全密级枚举 */
export enum SecurityLevel {
  /** 绝密 */
  TOP_SECRET = '绝密',
  /** 机密 */
  SECRET = '机密',
  /** 秘密 */
  CONFIDENTIAL = '秘密',
  /** 内部 */
  INTERNAL = '内部',
  /** 公开 */
  PUBLIC = '公开',
}

/** 密级对应的 Element Plus Tag 类型 */
export function getSecurityLevelTagType(level: SecurityLevel): string {
  switch (level) {
    case SecurityLevel.TOP_SECRET:
      return 'danger'
    case SecurityLevel.SECRET:
      return 'warning'
    case SecurityLevel.CONFIDENTIAL:
      return 'primary'
    case SecurityLevel.INTERNAL:
      return 'info'
    default:
      return ''
  }
}

/** 密级排序权重（越高越敏感） */
export function getSecurityWeight(level: SecurityLevel): number {
  switch (level) {
    case SecurityLevel.TOP_SECRET:
      return 5
    case SecurityLevel.SECRET:
      return 4
    case SecurityLevel.CONFIDENTIAL:
      return 3
    case SecurityLevel.INTERNAL:
      return 2
    case SecurityLevel.PUBLIC:
      return 1
    default:
      return 0
  }
}

/** 简易 XSS 过滤 */
export function sanitizeInput(input: string): string {
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}
