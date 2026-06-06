import { get, post, put, del, apiRequest } from "./request";
import api from "./request"; // keep for blob-only calls

/** 将 Blob 响应触发为浏览器文件下载 */
function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

// ── List / detail ──
export const getSupportedVillages = (params?: any) =>
  get("/supported-villages", params);
export const getSupportedVillage = (id: number) =>
  get("/supported-villages/" + id);

// ── CRUD ──
export const createSupportedVillage = (data: any) =>
  post("/supported-villages", data);
export const updateSupportedVillage = (id: number, data: any) =>
  put("/supported-villages/" + id, data);
export const deleteSupportedVillage = (id: number) =>
  del("/supported-villages/" + id);
export const batchDeleteSupportedVillages = (ids: number[]) =>
  post("/supported-villages/batch-delete", { ids });

// ── Import / export ──
export const importSupportedVillages = (file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequest({
    method: "POST",
    url: "/supported-villages/import",
    data: fd,
    headers: { "Content-Type": "multipart/form-data" },
  });
};
// blob 响应：触发浏览器下载
export const exportSupportedVillages = (params?: any) =>
  api
    .get("/supported-villages/export", { params, responseType: "blob" })
    .then((r) => {
      const disp = r.headers?.["content-disposition"] || "";
      const m = disp.match(/filename[^;=\n]*=["']?([^"';\n]*)["']?/);
      triggerDownload(r.data, m?.[1] || "supported_villages_export.xlsx");
    });
export const downloadImportTemplate = () =>
  api
    .get("/supported-villages/import-template", { responseType: "blob" })
    .then((r) => {
      triggerDownload(r.data, "帮扶村导入模板.xlsx");
    });
export const downloadTemplate = downloadImportTemplate;

// ── Filter options ──
export const getFilterOptions = () => get("/supported-villages/filter-options");
export const getChangeHistory = (_villageId: number) => Promise.resolve([]);

// ── Yearly data ──
export const getYearlyData = (villageId: number, year: number) =>
  get(`/supported-villages/${villageId}/yearly/${year}`);
export const copyYearData = (
  villageId: number,
  fromYear: number,
  toYear: number,
) => post(`/supported-villages/${villageId}/yearly/copy`, { fromYear, toYear });

export const saveYearlySectionData = (
  villageId: number,
  year: number,
  section: string,
  data: any,
) => post(`/supported-villages/${villageId}/yearly/${year}/${section}`, data);

// Backward compat aliases
export const saveIncomeData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "income", d);
export const saveIndustryData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "industry", d);
export const saveInfrastructureData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "infrastructure", d);
export const saveEducationData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "education", d);
export const saveForceInvestmentData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "force-investment", d);
export const savePartyBuildingData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "party-building", d);
export const saveMedicalData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "medical", d);
export const saveConsumptionData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "consumption", d);
export const saveEmploymentData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "employment", d);
export const savePopulationData = (v: number, y: number, d: any) =>
  saveYearlySectionData(v, y, "population", d);

// ── Sections ──
export const getSectionAttachments = (villageId: number, section: string) =>
  get(`/supported-villages/${villageId}/sections/${section}/attachments`);
export const saveSectionData = (
  villageId: number,
  section: string,
  data: any,
) => post(`/supported-villages/${villageId}/sections/${section}`, data);
export const saveCommitteeData = (villageId: number, data: any) =>
  post(`/supported-villages/${villageId}/committee`, data);
export const uploadSectionAttachment = (
  villageId: number,
  section: string,
  file: File,
) => {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequest({
    method: "POST",
    url: `/supported-villages/${villageId}/sections/${section}/attachments`,
    data: fd,
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const deleteSectionAttachment = (
  villageId: number,
  section: string,
  attachmentId: number,
) =>
  del(
    `/supported-villages/${villageId}/sections/${section}/attachments/${attachmentId}`,
  );

// ── Transition funding ──
export const getTransitionFunding = (villageId: number) =>
  get(`/supported-villages/${villageId}/transition-funding`);
export const saveTransitionFunding = (villageId: number, data: any) =>
  post(`/supported-villages/${villageId}/transition-funding`, data);

// ── Import (yearly overview) ──
export const importSectionData = (villageId: number, file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequest({
    method: "POST",
    url: `/supported-villages/${villageId}/sections/import`,
    data: fd,
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const downloadAllTemplates = () =>
  api
    .get("/supported-villages/templates/all", { responseType: "blob" })
    .then((r) => {
      triggerDownload(r.data, "全部板块模板.xlsx");
    });
export const importAllSectionsData = (villageId: number, file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return apiRequest({
    method: "POST",
    url: `/supported-villages/${villageId}/sections/import-all`,
    data: fd,
    headers: { "Content-Type": "multipart/form-data" },
  });
};
