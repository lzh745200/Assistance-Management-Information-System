/**
 * API 缓存 Composable
 */
import { ref } from "vue";

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

export function useApiCache<T = any>(ttlMs = 60000) {
  const cache = ref<Map<string, CacheEntry<T>>>(new Map());

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
