import api from "./request";
export const systemHealthApi = {
  overview: () => api.get("/system/health/overview"),
  liveness: () => api.get("/system/health/liveness"),
  readiness: () => api.get("/system/health/readiness"),
  metrics: () => api.get("/system/health/metrics"),
};
