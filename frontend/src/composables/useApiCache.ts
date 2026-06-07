/**
 * API 缓存 Composable
 *
 * 使用 shallowRef 避免 Vue 深度响应式包裹泛型 Map，
 * 防止 UnwrapRef<T> 类型推断问题。
 */
import { shallowRef } from "vue";

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

export function useApiCache<T = any>(ttlMs = 60000) {
  const cache = shallowRef<Map<string, CacheEntry<T>>>(new Map());

  function get(key: string): T | null {
    const entry = cache.value.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > ttlMs) {
      cache.value.delete(key);
      return null;
    }
    return entry.data;
  }

  function set(key: string, data: T) {
    cache.value.set(key, { data, timestamp: Date.now() });
  }

  function invalidate(key?: string) {
    if (key) {
      cache.value.delete(key);
    } else {
      cache.value.clear();
    }
  }

  return { get, set, invalidate };
}
