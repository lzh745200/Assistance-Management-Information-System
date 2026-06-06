import api from "./request";

export type CreateOrganizationPassCodeRequest = {
  organization_id: number;
  verification_code: string;
  allow_subordinate_generation?: boolean;
  description?: string;
};

export type OrganizationPassCodeResponse = {
  id: number;
  organization_id: number;
  organization_name?: string;
  pass_code: string;
  status: string;
  created_at?: string;
  expires_at?: string;
  description?: string;
};

export const orgPassCodeApi = {
  generate: (orgId: number) =>
    api.post("/organizations/" + orgId + "/passcode"),
  verify: (code: string) =>
    api.post("/organizations/passcode/verify", { code }),
};

export const getOrganizationVerificationCode = (orgId: number) =>
  api.get(`/organizations/${orgId}/verification-code`);

export const createOrganizationPassCode = (
  data: CreateOrganizationPassCodeRequest,
) => api.post("/organizations/passcodes", data);

export const getOrganizationPassCodeList = (params?: {
  organization_id?: number;
  status?: string;
  page?: number;
  page_size?: number;
}) => api.get("/organizations/passcodes", { params });

export const exportOrganizationPassCodes = (params?: {
  organization_id?: number;
  status?: string;
}) =>
  api
    .get("/organizations/passcodes/export", {
      params,
      responseType: "blob",
    })
    .then((r) => {
      const url = window.URL.createObjectURL(r.data as Blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "组织通行证码.xlsx";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    });
