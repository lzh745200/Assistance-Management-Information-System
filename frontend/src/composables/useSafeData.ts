/**
 * useSafeData — API 脏数据安全访问工具
 *
 * 防御性类型守卫：确保从 API 获取的数据字段具有安全的类型和默认值。
 * 不修改原始数据，返回安全的副本或默认值。
 */

/** 确保值为数组，否则返回空数组 */
export function safeArray<T = unknown>(value: unknown, fallback: T[] = []): T[] {
  return Array.isArray(value) ? (value as T[]) : fallback
}

/** 确保值为非数组对象，否则返回默认对象 */
export function safeObject<T extends Record<string, unknown>>(value: unknown, fallback: T): T {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as T
  }
  return fallback
}

/** 确保值为字符串，否则返回空字符串 */
export function safeString(value: unknown, fallback: string = ''): string {
  return typeof value === 'string' ? value : fallback
}

/** 确保值为有效数字，NaN/Infinity/undefined/null → 默认值 */
export function safeNumber(value: unknown, fallback: number = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}
