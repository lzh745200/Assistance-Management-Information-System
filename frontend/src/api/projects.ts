import api from "./request";

function triggerDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename;
  document.body.appendChild(link); link.click();
  document.body.removeChild(link); window.URL.revokeObjectURL(url);
}

// Types
export interface Project {
  id: number;
  name: string;
  status: string;
  village_id?: number;
  description?: string;
  budget?: number;
  start_date?: string;
  end_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateProjectRequest {
  name: string;
  village_id: number;
  status?: string;
  description?: string;
  budget?: number;
  start_date?: string;
  end_date?: string;
}

// Core API
export const projectsApi = {
  list: (params?: any) => api.get("/projects", { params }),
  get: (id: number) => api.get("/projects/" + id),
  create: (data: any) => api.post("/projects", data),
  update: (id: number, data: any) => api.put("/projects/" + id, data),
  delete: (id: number) => api.delete("/projects/" + id),
  getById: (id: number) => api.get("/projects/" + id),
  getStats: () => api.get("/projects/stats"),
  exportList: (params?: any) => api.get("/projects/export", { params, responseType: "blob" }).then(r => triggerDownload(r.data, "帮扶项目导出.xlsx")),
  importData: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/projects/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  uploadFiles: (id: number, files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    return api.post("/projects/" + id + "/files", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  listFiles: (id: number) => api.get("/projects/" + id + "/files"),
  getFileDownloadUrl: (projectId: number, fileId: number) =>
    "/api/v1/projects/" + projectId + "/files/" + fileId + "/download",
  deleteFile: (projectId: number, fileId: number) =>
    api.delete("/projects/" + projectId + "/files/" + fileId),
};

// Alias for views that use the singular form
export const projectApi = projectsApi;
