import { defineStore } from "pinia";
import { ref } from "vue";

export const useDataStore = defineStore("data", () => {
  const dataList = ref<any[]>([]);
  const currentData = ref<any>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const total = ref(0);

  async function fetchData(_params?: any) {
    loading.value = true;
    error.value = null;
    try {
      // Stub
      total.value = 0;
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  function setCurrentData(data: any) {
    currentData.value = data;
  }

  return {
    dataList,
    currentData,
    loading,
    error,
    total,
    fetchData,
    setCurrentData,
  };
});
