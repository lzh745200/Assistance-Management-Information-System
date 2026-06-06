/** API 响应解包工具 — 处理后端多种响应格式 */

export interface UnwrappedList {
  items: any[];
  total: number;
}

/** 从 axios 解包后的 data 中提取 items + total
 *
 * 兼容格式:
 *   { items, total }     — 直接分页格式
 *   { code, data: { items, total } } — 标准 API 响应
 */
export function unwrapList(res: any): UnwrappedList {
  if (res?.items)
    return { items: res.items, total: res.total ?? res.items.length };
  if (res?.data?.items)
    return {
      items: res.data.items,
      total: res.data.total ?? res.data.items.length,
    };
  return { items: [], total: 0 };
}
