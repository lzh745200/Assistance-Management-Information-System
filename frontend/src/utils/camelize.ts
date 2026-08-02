/**
 * 字段命名转换工具
 * 后端响应统一 snake_case,前端组件统一 camelCase。
 * 本工具在 api/request 出口对响应 data 载荷做 snake→camel 转换,
 * 单点收口,避免各组件手动处理。
 */

/** snake_case → camelCase */
export function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase())
}

/** camelCase → snake_case */
export function toSnakeCase(str: string): string {
  return str.replace(/([a-z0-9])([A-Z])/g, '$1_$2').toLowerCase()
}

// 不转换的顶层元数据键(信封字段与业务无关)
const META_KEYS = new Set([
  'code',
  'message',
  'success',
  'data',
  'items',
  'total',
  'page',
  'page_size',
])

/**
 * 深度转换对象键名(snake→camel),跳过信封元数据键。
 * 支持嵌套对象与数组。
 */
export function camelizeDeep(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(camelizeDeep)
  }
  if (obj !== null && typeof obj === 'object') {
    const out: Record<string, any> = {}
    for (const [k, v] of Object.entries(obj)) {
      const newKey = META_KEYS.has(k) ? k : toCamelCase(k)
      out[newKey] = camelizeDeep(v)
    }
    return out
  }
  return obj
}

/** 深度转换对象键名(camel→snake),用于请求体 */
export function snakeizeDeep(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(snakeizeDeep)
  }
  if (obj !== null && typeof obj === 'object') {
    const out: Record<string, any> = {}
    for (const [k, v] of Object.entries(obj)) {
      out[toSnakeCase(k)] = snakeizeDeep(v)
    }
    return out
  }
  return obj
}
