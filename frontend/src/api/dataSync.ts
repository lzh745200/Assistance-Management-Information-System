import api from "./request";

function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename;
  document.body.appendChild(link); link.click();
  document.body.removeChild(link); window.URL.revokeObjectURL(url);
}

// Types
export interface SyncLog {
  id: string;
  action: string;
  status: string;
  message?: string;
  created_at: string;
  task_id?: string;
}

export interface ImportDataResponse {
  success: boolean;
  count: number;
  message?: string;
  errors?: string[];
}

export interface ExportEncryptedParams {
  password: string;
  modules?: string[];
}

export interface ConflictDetail {
  id: string;
  entity_type: string;
  local_data: Record<string, any>;
  remote_data: Record<string, any>;
  resolved?: boolean;
}

// Named functions
export const importData = (file: File, strategy: string = "overwrite") => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("strategy", strategy);
  return api.post("/data-sync/import", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const importEncryptedData = (file: File, password: string) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("password", password);
  return api.post("/data-sync/import-encrypted", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const exportData = (params: any) =>
  api.post("/data-sync/export", params);

export const exportEncryptedData = (params: ExportEncryptedParams) =>
  api.post("/data-sync/export-encrypted", params);

export const downloadExportPackage = (packageId: string) =>
  api.get("/data-sync/download/" + packageId, { responseType: "blob" }).then(r => triggerDownload(r.data, "data_export_" + packageId + ".zip"));

export const getSyncLogs = (params?: any) =>
  api.get("/data-sync/logs", { params });

export const getConflicts = () =>
  api.get("/data-sync/conflicts");

export const resolveConflict = (id: string, resolution: string) =>
  api.post("/data-sync/conflicts/" + id + "/resolve", { resolution });

// Backward-compatible object form
export const dataSyncApi = {
  sync: (data: any) => api.post("/data-sync/sync", data),
  getStatus: (taskId: string) => api.get("/data-sync/status/" + taskId),
  importData,
  importEncryptedData,
  exportData,
  exportEncryptedData,
  downloadExportPackage,
  getSyncLogs,
  getConflicts,
  resolveConflict,
};




export const ImportDataResponse = () => Promise.resolve({});

export const SyncLog = () => Promise.resolve({});
