import api from "./request";

export const getOrganizations = (params?: any) =>
  api.get("/organizations", { params });
export const getOrganization = (id: number) => api.get("/organizations/" + id);
export const getOrganizationTree = () => api.get("/organizations/tree");
export const createOrganization = (data: any) =>
  api.post("/organizations", data);
export const updateOrganization = (id: number, data: any) =>
  api.put("/organizations/" + id, data);
export const deleteOrganization = (id: number) =>
  api.delete("/organizations/" + id);
export const batchUpdateSortOrders = (d: any[]) =>
  api.post("/organizations/batch-update-sort", d);

export const getMyOrganization = () =>
  api.get("/organizations/my-organization");

export const getSubordinates = () =>
  api.get("/organizations/subordinates");

export const getTypeOptions = () =>
  api.get("/organizations/types/options");

export const getChildren = (orgId: number) =>
  api.get(`/organizations/${orgId}/children`);

export const getAncestors = (orgId: number) =>
  api.get(`/organizations/${orgId}/ancestors`);

export const moveOrganization = (orgId: number, data: any) =>
  api.post(`/organizations/${orgId}/move`, data);

export const activateOrganization = (orgId: number) =>
  api.post(`/organizations/${orgId}/activate`);

export const deactivateOrganization = (orgId: number) =>
  api.post(`/organizations/${orgId}/deactivate`);
