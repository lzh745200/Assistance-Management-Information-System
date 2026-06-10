import api from "./request";

const fallbackIntegrityCheck = {
  data: { status: "error", messages: ["后端接口未就绪"] },
};

const fallbackTableStats = {
  data: { tables: [], total_tables: 0, total_rows: 0 },
};

export const systemHealthApi = {
  overview: () => api.get("/system/health/overview"),
  liveness: () => api.get("/system/health/liveness"),
  readiness: () => api.get("/system/health/readiness"),
  metrics: () => api.get("/system/health/metrics"),
  full: () => api.get("/system/health/full"),
  getTableStats: () =>
    api.get("/system/health/table-stats").catch(() => fallbackTableStats),
  runIntegrityCheck: () =>
    api.post("/system/health/integrity-check").catch(() => fallbackIntegrityCheck),
  runWalCheckpoint: () =>
    api.post("/system/health/wal-checkpoint").catch(() => fallbackIntegrityCheck),
  runVacuum: () =>
    api.post("/system/health/vacuum").catch(() => fallbackIntegrityCheck),
};
