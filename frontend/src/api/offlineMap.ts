import api from './request'

export const offlineMapApi = {
  getTiles: (z: number, x: number, y: number) => api.get(`/offline-map/tiles/${z}/${x}/${y}`),
  getStatus: () => api.get('/offline-map/status'),
}

export const clearTiles = () => api.delete('/offline-map/clear')

export const downloadTiles = (params: {
  min_lat: number
  max_lat: number
  min_lon: number
  max_lon: number
  min_zoom?: number
  max_zoom?: number
}) => api.post('/offline-map/download', null, { params })

export const getMapStatus = () => api.get('/offline-map/status')

export type MapCoverage = { area: string; zoom: number; tiles: number }
