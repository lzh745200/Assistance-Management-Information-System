/**
 * 黔南州地区常量和工具函数
 *
 * Feature: supported-village-enhancement
 * Requirements: 16.1, 16.2, 16.3
 */

/**
 * 黔南州12个县市列表
 * Requirements: 16.1
 */
export const QIANNAN_COUNTIES = [
  "都匀市",
  "长顺县",
  "独山县",
  "平塘县",
  "罗甸县",
  "惠水县",
  "贵定县",
  "福泉市",
  "瓮安县",
  "三都水族自治县",
  "荔波县",
  "龙里县",
] as const;

export type QiannanCounty = (typeof QIANNAN_COUNTIES)[number];

/**
 * 固定的省份值
 * Requirements: 16.2
 */
export const DEFAULT_PROVINCE = "贵州省";

/**
 * 固定的州/市值
 * Requirements: 16.2
 */
export const DEFAULT_CITY = "黔南布依族苗族自治州";

/**
 * Prefecture = City level in Chinese administrative divisions
 * Requirements: 16.2
 */
export const DEFAULT_PREFECTURE = DEFAULT_CITY;

/**
 * 验证县/市值是否有效
 * Requirements: 16.3
 */
export function isValidCounty(county: string): county is QiannanCounty {
  return QIANNAN_COUNTIES.includes(county as QiannanCounty);
}

/**
 * 获取完整的地区信息
 */
export function getFullRegionInfo(county: string) {
  return {
    province: DEFAULT_PROVINCE,
    city: DEFAULT_CITY,
    county: isValidCounty(county) ? county : "",
  };
}
