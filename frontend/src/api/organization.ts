import api from "./request";

export const getOrganizations = (params?: any) => api.get("/organizations", { params });
export const getOrganization = (id: number) => api.get("/organizations/" + id);
export const getOrganizationTree = () => api.get("/organizations/tree");
export const createOrganization = (data: any) => api.post("/organizations", data);
export const updateOrganization = (id: number, data: any) => api.put("/organizations/" + id, data);
export const deleteOrganization = (id: number) => api.delete("/organizations/" + id);
export const batchUpdateSortOrders = (d: any[]) => api.put("/organizations/sort", d);
