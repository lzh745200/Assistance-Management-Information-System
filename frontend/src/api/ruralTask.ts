import api from "./request";
export const ruralTaskApi = {
  // ========== 基础 CRUD ==========
  list: (p?: any) => api.get("/rural-tasks", { params: p }),
  get: (id: number) => api.get("/rural-tasks/" + id),
  create: (d: any) => api.post("/rural-tasks", d),
  update: (id: number, d: any) => api.put("/rural-tasks/" + id, d),
  delete: (id: number) => api.delete("/rural-tasks/" + id),

  // ========== 统计 ==========
  getStatistics: () => api.get("/rural-tasks/statistics"),

  // ========== 工作流 ==========
  submitTask: (id: number) => api.post(`/rural-tasks/${id}/submit`),
  approveTask: (id: number, data?: any) =>
    api.post(`/rural-tasks/${id}/approve`, data || {}),

  // ========== 批量操作 ==========
  batchDelete: (ids: number[]) =>
    api.post("/rural-tasks/batch-delete", { ids }),
};
