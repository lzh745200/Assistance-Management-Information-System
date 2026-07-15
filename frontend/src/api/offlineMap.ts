import { get, post, del } from '@/api/request'

export const offlineMapApi = {
  getTiles: (z: number, x: number, y: number) => get(`/offline-map/tiles/${z}/${x}/${y}`),
  getStatus: () => get('/offline-map/status'),
}

export const clearTiles = () => del('/offline-map/clear')

export const downloadTiles = (params: {
  min_lat: number
  max_lat: number
  min_lon: number
  max_lon: number
  min_zoom?: number
  max_zoom?: number
}) => post('/offline-map/download', null, { params })

export const getMapStatus = () => get('/offline-map/status')

export type MapCoverage = { area: string; zoom: number; tiles: number }
