/**
 * 批量操作 Composable
 */
import { ref, computed } from "vue";

export function useBatchOperation<T = any>() {
  const selectedItems = ref<Set<T>>(new Set());
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
