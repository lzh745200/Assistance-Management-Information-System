import api from "./request";
export const ruralTaskApi = {
  list: (p?: any) => api.get("/rural-tasks", { params: p }),
  get: (id: number) => api.get("/rural-tasks/" + id),
  create: (d: any) => api.post("/rural-tasks", d),
  update: (id: number, d: any) => api.put("/rural-tasks/" + id, d),
  delete: (id: number) => api.delete("/rural-tasks/" + id),
};
