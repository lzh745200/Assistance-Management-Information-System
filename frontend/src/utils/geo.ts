/**
 * 地理计算工具模块
 *
 * Haversine 距离、路线时间估算、坐标格式解析
 */

const EARTH_RADIUS_KM = 6371;
const RURAL_SPEED_KPH = 35; // 贵州山区平均车速
const ROAD_CURVATURE_FACTOR = 1.5; // 直线→道路距离系数

export interface LatLng {
  lat: number;
  lng: number;
}

export interface RouteResult {
  origin: LatLng;
  destination: LatLng;
  straightDistanceKm: number;
  estimatedRoadDistanceKm: number;
  estimatedDriveMinutes: number;
  formattedTime: string;
}

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

/** Haversine 大圆距离 (km) */
export function haversineDistance(a: LatLng, b: LatLng): number {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(h));
}

/** 计算路线估算（距离 + 驾驶时间） */
export function calculateRoute(origin: LatLng, dest: LatLng): RouteResult {
  const straightKm = haversineDistance(origin, dest);
  const roadKm = straightKm * ROAD_CURVATURE_FACTOR;
  const minutes = (roadKm / RURAL_SPEED_KPH) * 60;
  let formattedTime: string;
  if (minutes < 1) formattedTime = "< 1 分钟";
  else if (minutes < 60) formattedTime = `约 ${Math.round(minutes)} 分钟`;
  else
    formattedTime = `约 ${Math.floor(minutes / 60)} 小时 ${Math.round(minutes % 60)} 分钟`;
  return {
    origin,
    destination: dest,
    straightDistanceKm: Math.round(straightKm * 10) / 10,
    estimatedRoadDistanceKm: Math.round(roadKm * 10) / 10,
    estimatedDriveMinutes: Math.round(minutes),
    formattedTime,
  };
}

/** 解析坐标: "26.5,107.5" 或 "26.5, 107.5" */
export function parseCoordinate(input: string): LatLng | null {
  const m = /^(-?\d+\.?\d*)\s*[,，]\s*(-?\d+\.?\d*)$/.exec(input.trim());
  if (m) {
    const lat = parseFloat(m[1]),
      lng = parseFloat(m[2]);
    if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180)
      return { lat, lng };
  }
  return null;
}
