import { defineStore } from "pinia";
import { ref } from "vue";
import { post, put, del, apiRequest } from "@/api/request";
import { unwrapList } from "@/utils/unwrapList";

export const useFundsStore = defineStore("funds", () => {
  const fundList = ref<any[]>([]);
  const current = ref<any>(null);
  const loading = ref(false);
  const total = ref(0);

  async function fetchFunds(params?: any) {
    loading.value = true;
    try {
      const res = await apiRequest<any>({
        method: "GET",
        url: "/funds",
        params,
        timeout: 15000,
      });
      const { items, total: t } = unwrapList(res);
      fundList.value = items;
      total.value = t;
    } catch {
      fundList.value = [];
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  async function createFund(data: any) {
    await post<any>("/funds", data);
    await fetchFunds();
  }

  async function updateFund(id: number, data: any) {
    await put<any>("/funds/" + id, data);
    const idx = fundList.value.findIndex((f: any) => f.id === id);
    if (idx >= 0) fundList.value[idx] = { ...fundList.value[idx], ...data };
  }

  async function deleteFund(id: number) {
    await del<any>("/funds/" + id);
    fundList.value = fundList.value.filter((f: any) => f.id !== id);
    total.value--;
  }

  async function getSummary() {
    try {
      const res = await apiRequest<any>({
        method: "GET",
        url: "/funds/statistics/overview",
        timeout: 10000,
      });
      return res?.data ?? res ?? {};
    } catch {
      return {
        total_amount: 0,
        total_allocated: 0,
        total_count: 0,
        by_status: {},
      };
    }
  }

  async function approveFund(id: number) {
    await post<any>("/funds/approve/" + id, {});
    const idx = fundList.value.findIndex((f: any) => f.id === id);
    if (idx >= 0) fundList.value[idx].status = "approved";
  }

  return {
    fundList,
    current,
    loading,
    total,
    fetchFunds,
    createFund,
    updateFund,
    deleteFund,
    getSummary,
    approveFund,
  };
});
