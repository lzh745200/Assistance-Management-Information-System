import api from "./request";

// Types
export type WorkStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "delayed"
  | "cancelled";

export type WorkType =
  | "industry"
  | "infrastructure"
  | "education"
  | "medical"
  | "party"
  | "consumption"
  | "employment"
  | "other"
  | "party_building"
  | "ecommerce"
  | "talent";

export interface WorkReportData {
  summary: Record<string, any>;
  details: any[];
  generated_at: string;
}

// Named functions
export const getRuralWorks = (params?: any) =>
  api.get("/rural-works", { params });

export const createRuralWork = (data: any) =>
  api.post("/rural-works", data);

export const updateRuralWork = (id: number, data: any) =>
  api.put("/rural-works/" + id, data);

export const deleteRuralWork = (id: number) =>
  api.delete("/rural-works/" + id);

export const generateWorkReport = (params?: any) =>
  api.get("/rural-works/report", { params });

// Backward-compatible object form
export const ruralWorkApi = {
  list: (params?: any) => api.get("/rural-works", { params }),
  get: (id: number) => api.get("/rural-works/" + id),
  create: (data: any) => api.post("/rural-works", data),
  update: (id: number, data: any) => api.put("/rural-works/" + id, data),
  delete: deleteRuralWork,
  getRuralWorks,
  createRuralWork,
  updateRuralWork,
  deleteRuralWork,
  generateWorkReport,
};
