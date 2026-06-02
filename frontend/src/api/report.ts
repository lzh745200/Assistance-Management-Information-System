import api from "./request";
export const reportApi = { list: (p?:any) => api.get("/reports",{params:p}), generate: (d:any) => api.post("/reports/generate",d), download: (id:number) => api.get("/reports/"+id+"/download",{responseType:"blob"}) };
