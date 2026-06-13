import api from "./request";

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
  // ========== 基础 CRUD ==========
  list: (params?: any) => api.get("/projects", { params }),
  get: (id: number) => api.get("/projects/" + id),
  create: (data: any) => api.post("/projects", data),
  update: (id: number, data: any) => api.put("/projects/" + id, data),
  delete: (id: number) => api.delete("/projects/" + id),
  getById: (id: number) => api.get("/projects/" + id),
  getStats: () => api.get("/projects/stats"),
  exportList: (params?: any) =>
    api.get("/projects/export", { params, responseType: "blob" }),
  importData: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/projects/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // ========== 项目文件 ==========
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
  previewFile: (projectId: number, fileId: number) =>
    api.get(`/projects/${projectId}/files/${fileId}/preview`),

  // ========== 项目变更历史 ==========
  getChangeHistory: (projectId: number) =>
    api.get(`/projects/${projectId}/history/changes`),

  // ========== 项目经费关联 ==========
  getFunds: (projectId: number) =>
    api.get(`/projects/${projectId}/funds`),
  addFund: (projectId: number, data: any) =>
    api.post(`/projects/${projectId}/funds`, data),

  // ========== 项目任务 ==========
  getTasks: (projectId: number) =>
    api.get(`/projects/${projectId}/tasks`),
  createTask: (projectId: number, data: any) =>
    api.post(`/projects/${projectId}/tasks`, data),
  updateTask: (projectId: number, taskId: number, data: any) =>
    api.put(`/projects/${projectId}/tasks/${taskId}`, data),
  deleteTask: (projectId: number, taskId: number) =>
    api.delete(`/projects/${projectId}/tasks/${taskId}`),
};

// Alias for views that use the singular form
export const projectApi = projectsApi;
