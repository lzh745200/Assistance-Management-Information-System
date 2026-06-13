import api from "./request";

export const schoolsApi = {
  // ========== 基础 CRUD ==========
  list: (p?: any) => api.get("/schools", { params: p }),
  get: (id: number) => api.get("/schools/" + id),
  create: (d: any) => api.post("/schools", d),
  update: (id: number, d: any) => api.put("/schools/" + id, d),
  delete: (id: number) => api.delete("/schools/" + id),

  // ========== 统计与选项 ==========
  getStatistics: () => api.get("/schools/statistics"),
  getTypeOptions: () => api.get("/schools/options/types"),
  getStatusOptions: () => api.get("/schools/options/statuses"),

  // ========== 导入导出 ==========
  importExcel: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post("/schools/import/excel", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  exportExcel: (params?: any) =>
    api.get("/schools/export/excel", { params, responseType: "blob" }),
  downloadImportTemplate: () =>
    api.get("/import/template", { params: { entity_type: "school" }, responseType: "blob" }),

  // ========== 学校帮扶项目 ==========
  listProjects: (schoolId: number | string) =>
    api.get(`/schools/${schoolId}/projects`),
  createProject: (schoolId: number | string, data: any) =>
    api.post(`/schools/${schoolId}/projects`, data),
  updateProject: (schoolId: number | string, projectId: number | string, data: any) =>
    api.put(`/schools/${schoolId}/projects/${projectId}`, data),
  deleteProject: (schoolId: number | string, projectId: number | string) =>
    api.delete(`/schools/${schoolId}/projects/${projectId}`),

  // ========== 资助学生 ==========
  listScholarshipStudents: (schoolId: number | string, year?: number) =>
    api.get(`/schools/${schoolId}/scholarship-students`, { params: year !== undefined ? { year } : undefined }),
  createScholarshipStudent: (schoolId: number | string, data: any) =>
    api.post(`/schools/${schoolId}/scholarship-students`, data),
  updateScholarshipStudent: (
    schoolId: number | string,
    studentId: number | string,
    data: any,
  ) => api.put(`/schools/${schoolId}/scholarship-students/${studentId}`, data),
  deleteScholarshipStudent: (schoolId: number | string, studentId: number | string) =>
    api.delete(`/schools/${schoolId}/scholarship-students/${studentId}`),
  importScholarshipStudents: (schoolId: number | string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post(`/schools/${schoolId}/scholarship-students/import`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // ========== 附件管理 ==========
  listAttachments: (schoolId: number | string) =>
    api.get(`/schools/${schoolId}/attachments`),
  uploadAttachment: (schoolId: number | string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return api.post(`/schools/${schoolId}/attachments`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteAttachment: (attachmentId: number | string) =>
    api.delete(`/schools/attachments/${attachmentId}`),
  downloadAttachment: (attachmentId: number | string) =>
    api.get(`/schools/attachments/${attachmentId}/download`, { responseType: "blob" }),
};

export const schoolApi = schoolsApi;
