/**
 * 批量操作 Composable
 *
 * 使用 shallowRef 避免 Vue 深度响应式包裹泛型 Set，
 * 防止 UnwrapRef<T> 类型推断问题。
 * 注意：shallowRef 只追踪 .value 替换，不追踪 Set 内部变更，
 * 因此每次增删后需重新赋值（new Set(set)）。
 */
import { shallowRef, ref, computed } from "vue";

export function useBatchOperation<T = any>() {
  const selectedItems = shallowRef<Set<T>>(new Set());
  const isAllSelected = ref(false);

  const selectedCount = computed(() => selectedItems.value.size);

  function toggleSelect(item: T) {
    const set = selectedItems.value;
    if (set.has(item)) {
      set.delete(item);
    } else {
      set.add(item);
    }
    selectedItems.value = new Set(set);
    isAllSelected.value = false;
  }

  function selectAll(items: T[]) {
    selectedItems.value = new Set(items);
    isAllSelected.value = true;
  }

  function clearSelection() {
    selectedItems.value = new Set();
    isAllSelected.value = false;
  }

  function getSelectedList(): T[] {
    return Array.from(selectedItems.value);
  }

  return {
    selectedItems,
    isAllSelected,
    selectedCount,
    toggleSelect,
    selectAll,
    clearSelection,
    getSelectedList,
  };
}
