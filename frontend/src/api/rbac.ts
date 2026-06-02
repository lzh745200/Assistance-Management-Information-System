import api from "./request";
export const rbacApi = { getRoles: () => api.get("/rbac/roles"), getPermissions: () => api.get("/rbac/permissions"), assignRole: (userId:number,roleId:number) => api.post("/rbac/assign",{userId,roleId}) };
