import api from "./request";
export const orgPassCodeApi = { generate: (orgId:number) => api.post("/organizations/"+orgId+"/passcode"), verify: (code:string) => api.post("/organizations/passcode/verify",{code}) };
