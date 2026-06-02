import { defineStore } from "pinia";
import { ref } from "vue";
import { get, post, put, del } from "@/api/request";

export const usePolicyStore = defineStore("policy", () => {
  const policyList = ref<any[]>([]);
  const current = ref<any>(null);
  const loading = ref(false);
  const total = ref(0);

  async function fetchPolicies(params?: any) {
    loading.value = true;
    try {
      const res = await get<{ code: number; data: any[]; total?: number }>("/policies", { params });
      if (res.code === 200 && res.data) {
        policyList.value = res.data;
        total.value = res.total || res.data.length;
      }
    } catch { /* silent */ }
    finally { loading.value = false; }
  }

  async function fetchPolicy(id: number) {
    loading.value = true;
    try {
      const res = await get<{ code: number; data: any }>("/policies/" + id);
      if (res.code === 200) current.value = res.data;
    } catch { /* silent */ }
    finally { loading.value = false; }
  }

  async function createPolicy(data: any) {
    const res = await post("/policies", data);
    if (res.code === 200 && res.data) {
      policyList.value.unshift(res.data);
      total.value++;
    }
    return res;
  }

  async function updatePolicy(id: number, data: any) {
    const res = await put("/policies/" + id, data);
    if (res.code === 200) {
      const idx = policyList.value.findIndex((p: any) => p.id === id);
      if (idx >= 0) policyList.value[idx] = { ...policyList.value[idx], ...data };
    }
    return res;
  }

  async function deletePolicy(id: number) {
    const res = await del("/policies/" + id);
    if (res.code === 200) {
      policyList.value = policyList.value.filter((p: any) => p.id !== id);
      total.value--;
    }
    return res;
  }

  return { policyList, current, loading, total, fetchPolicies, fetchPolicy, createPolicy, updatePolicy, deletePolicy };
});
