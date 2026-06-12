/**
 * API 响应展开工具
 *
 * 后端大部分 JSON 端点返回 {data: payload, message: "..."} 格式。
 * 此函数将内层 data 提取到顶层，消除调用方的手动展开。
 *
 * @example
 *   const village = unwrapData(await getSupportedVillage(id));
 *   // village is now {id, name, ...} instead of {data: {id, name, ...}}
 */
export function unwrapData<T = Record<string, unknown>>(
  raw: unknown,
  fallback: T = {} as T,
): T {
  if (raw && typeof raw === "object" && "data" in raw) {
    return ((raw as Record<string, unknown>).data ?? raw) as T;
  }
  return (raw ?? fallback) as T;
}

export default unwrapData;
