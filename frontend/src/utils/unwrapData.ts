/**
 * API 响应展开工具
 *
 * @deprecated 自 request.ts 拦截器自动展开 {data: payload} 后，
 *             此函数已冗余。推荐直接使用 API 返回值（字段已在顶层）。
 *             现有调用方无需立即迁移，但新代码不应再引入 unwrapData。
 *
 * @example
 *   // 旧（仍可用但多余）:
 *   const village = unwrapData(await getSupportedVillage(id));
 *   // 新（推荐）:
 *   const village = await getSupportedVillage(id);
 */
export function unwrapData<T = Record<string, unknown>>(raw: unknown, fallback: T = {} as T): T {
  if (raw && typeof raw === 'object' && 'data' in raw) {
    const inner = (raw as Record<string, unknown>).data
    // 使用 || 而非 ?? 保持向后兼容：data=null/0/\"\"/false 时回退到 raw
    return (inner || raw) as T
  }
  return (raw || fallback) as T
}

export default unwrapData
