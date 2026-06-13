import api from "./request";

export const systemHealthApi = {
  overview: () => api.get("/health/overview"),
  database: () => api.get("/health/database"),
  liveness: () => api.get("/health/liveness"),
  readiness: () => api.get("/health/readiness"),
  full: () => api.get("/health/full"),
};
