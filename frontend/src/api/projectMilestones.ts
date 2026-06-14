import api from "./request";

export const projectMilestonesApi = {
  // ========== 里程碑 CRUD ==========
  list: (projectId: number) =>
    api.get("/projects/" + projectId + "/milestones"),
  create: (projectId: number, d: any) =>
    api.post("/projects/" + projectId + "/milestones", d),
  update: (projectId: number, id: number, d: any) =>
    api.put("/projects/" + projectId + "/milestones/" + id, d),
  delete: (projectId: number, id: number) =>
    api.delete("/projects/" + projectId + "/milestones/" + id),

  // ========== 状态转换 ==========
  getTransitionRules: (projectId: number) =>
    api.get(`/projects/${projectId}/transition-rules`),
  transitionStatus: (projectId: number, data: any) =>
    api.post(`/projects/${projectId}/transition`, data),

  // ========== 变更日志 ==========
  getChangeLogs: (projectId: number) =>
    api.get(`/projects/${projectId}/change-logs`),

  // ========== 仪表板 ==========
  getUpcomingMilestones: () =>
    api.get("/projects/dashboard/upcoming-milestones"),
  getOverdueMilestones: () => api.get("/projects/dashboard/overdue-milestones"),
};
