import api from "./request";
export const schoolsApi = {
  list: (p?: any) => api.get("/schools", { params: p }),
  get: (id: number) => api.get("/schools/" + id),
  create: (d: any) => api.post("/schools", d),
  update: (id: number, d: any) => api.put("/schools/" + id, d),
  delete: (id: number) => api.delete("/schools/" + id),
};
export const schoolApi = schoolsApi;
