import api from "./request";
export const offlineMapApi = {
  getTiles: () => api.get("/offline-map/tiles"),
  getStatus: () => api.get("/offline-map/status"),
};

export const clearTiles = () => api.delete("/offline-map/tiles");

export const downloadTiles = (area: string) =>
  api.post("/offline-map/tiles/download", { area });

export const getMapStatus = () => api.get("/offline-map/status");

export type MapCoverage = { area: string; zoom: number; tiles: number };
