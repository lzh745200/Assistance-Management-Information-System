import { defineStore } from "pinia";
import { ref } from "vue";

export const useIndustryStore = defineStore("industry", () => {
  const industryList = ref<any[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchIndustries(_params?: any) {
    loading.value = true;
    error.value = null;
    try {
      // Stub
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }

  return { industryList, loading, error, fetchIndustries };
});
