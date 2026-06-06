import api from "./request";
export const projectMilestonesApi = {
  list: (projectId: number) =>
    api.get("/projects/" + projectId + "/milestones"),
  create: (projectId: number, d: any) =>
    api.post("/projects/" + projectId + "/milestones", d),
  update: (projectId: number, id: number, d: any) =>
    api.put("/projects/" + projectId + "/milestones/" + id, d),
  delete: (projectId: number, id: number) =>
    api.delete("/projects/" + projectId + "/milestones/" + id),
};
