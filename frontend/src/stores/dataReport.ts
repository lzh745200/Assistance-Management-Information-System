import { defineStore } from "pinia";
import { ref } from "vue";
import { apiRequest } from "@/api/request";
import { unwrapList } from "@/utils/unwrapList";

export const useDataReportStore = defineStore("dataReport", () => {
  const reports = ref<any[]>([]);
  const currentReport = ref<any>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 接收的数据上报
  const receivedReports = ref<any[]>([]);
  const receivedTotal = ref(0);

  /** 获取接收到的上报列表 */
  async function fetchReceivedReports(params?: any) {
    loading.value = true;
    error.value = null;
    try {
      const res = await apiRequest<any>({
        method: "GET",
        url: "/data-reports/received",
        params,
        timeout: 15000,
      });
      const { items, total: t } = unwrapList(res);
      receivedReports.value = items;
      receivedTotal.value = t;
    } catch (e: any) {
      error.value = e?.response?.data?.message || e?.message || "加载失败";
      receivedReports.value = [];
      receivedTotal.value = 0;
    } finally {
      loading.value = false;
    }
  }

  /** 获取上报列表（通用） */
  async function fetchReports(params?: any) {
    loading.value = true;
    error.value = null;
    try {
      const res = await apiRequest<any>({
        method: "GET",
        url: "/data-reports",
        params,
        timeout: 15000,
      });
      const { items } = unwrapList(res);
      reports.value = items;
    } catch (e: any) {
      error.value = e?.message || "加载失败";
    } finally {
      loading.value = false;
    }
  }

  /** 预览上报数据 */
  async function previewReport(reportId: number) {
    const res = await apiRequest<any>({
      method: "GET",
      url: `/data-reports/${reportId}`,
      timeout: 10000,
    });
    return res;
  }

  /** 接收/批准上报 */
  async function receiveReport(reportId: number) {
    await apiRequest<any>({
      method: "POST",
      url: `/data-reports/${reportId}/approve`,
      timeout: 15000,
    });
  }

  /** 拒绝上报 */
  async function rejectReport(reportId: number, reason: string) {
    await apiRequest<any>({
      method: "POST",
      url: `/data-reports/${reportId}/review`,
      data: { decision: "reject", comment: reason },
      timeout: 10000,
    });
  }

  /** 下载上报数据包 */
  async function downloadReport(reportId: number) {
    const res = await apiRequest<any>({
      method: "GET",
      url: `/data-reports/${reportId}/package`,
      timeout: 10000,
    });
    return res;
  }

  /** 提交上报 */
  async function submitReport(data: any) {
    await apiRequest<any>({
      method: "POST",
      url: "/data-reports",
      data,
      timeout: 15000,
    });
  }

  return {
    reports, currentReport, loading, error,
    receivedReports, receivedTotal,
    fetchReports, fetchReceivedReports,
    previewReport, receiveReport, rejectReport, downloadReport,
    submitReport,
  };
});
