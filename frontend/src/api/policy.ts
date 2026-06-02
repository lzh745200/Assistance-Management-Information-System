import api from "./request";

function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename;
  document.body.appendChild(link); link.click();
  document.body.removeChild(link); window.URL.revokeObjectURL(url);
}

// ── Query ──
export const getLevelOptions = () => api.get("/policies/level-options");
export const getPolicyTypes = () => api.get("/policies/types");
export const searchPolicies = (query: string) => api.get("/policies/search", { params: { q: query } });
export const getPolicyCategories = () => api.get("/policies/categories");
export const getPolicyStats = () => api.get("/policies/stats");

// ── CRUD ──
export const getPolicies = (params?: any) => api.get("/policies", { params });
export const getPolicy = (id: number) => api.get("/policies/" + id);
export const createPolicy = (data: any) => api.post("/policies", data);
export const updatePolicy = (id: number, data: any) => api.put("/policies/" + id, data);
export const deletePolicy = (id: number) => api.delete("/policies/" + id);

// ── Import/export ──
export const importPolicies = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return api.post("/policies/import", fd, { headers: { "Content-Type": "multipart/form-data" } });
};
export const exportPolicies = (params?: any) => api.get("/policies/export", { params, responseType: "blob" }).then(r => triggerDownload(r.data, "帮扶政策导出.xlsx"));
export const exportPoliciesPDF = (params?: any) => api.get("/policies/export-pdf", { params, responseType: "blob" }).then(r => triggerDownload(r.data, "帮扶政策导出.pdf"));
export const exportPoliciesWPS = (params?: any) => api.get("/policies/export-wps", { params, responseType: "blob" }).then(r => triggerDownload(r.data, "帮扶政策导出.wps"));
export const downloadImportTemplate = () => api.get("/policies/import-template", { responseType: "blob" }).then(r => triggerDownload(r.data, "政策导入模板.xlsx"));

// ── Display helpers (used by views for status/label formatting) ──
const CATEGORY_LABELS: Record<string, string> = {};
const LEVEL_LABELS: Record<string, string> = {};
const STATUS_LABELS: Record<string, string> = {};
const STATUS_COLORS: Record<string, string> = {};

export const getCategoryLabel = (cat: string) => CATEGORY_LABELS[cat] || cat;
export const getLevelLabel = (level: string) => LEVEL_LABELS[level] || level;
export const getStatusLabel = (status: string) => STATUS_LABELS[status] || status;
export const getStatusColor = (status: string) => STATUS_COLORS[status] || "info";
