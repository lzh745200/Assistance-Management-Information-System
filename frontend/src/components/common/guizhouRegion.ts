/**
 * 贵州省行政区划数据
 * 包含全省 9 个市州及其下辖县市区（共 88 个县级行政区）
 */

export interface CityData {
  name: string;
  counties: string[];
}

/** 贵州省 9 个市州及下辖县市区 */
export const GUIZHOU_REGION: CityData[] = [
  {
    name: "贵阳市",
    counties: [
      "南明区",
      "云岩区",
      "花溪区",
      "乌当区",
      "白云区",
      "观山湖区",
      "开阳县",
      "息烽县",
      "修文县",
      "清镇市",
    ],
  },
  {
    name: "六盘水市",
    counties: ["钟山区", "六枝特区", "水城区", "盘州市"],
  },
  {
    name: "遵义市",
    counties: [
      "红花岗区",
      "汇川区",
      "播州区",
      "桐梓县",
      "绥阳县",
      "正安县",
      "道真仡佬族苗族自治县",
      "务川仡佬族苗族自治县",
      "凤冈县",
      "湄潭县",
      "余庆县",
      "习水县",
      "赤水市",
      "仁怀市",
    ],
  },
  {
    name: "安顺市",
    counties: [
      "西秀区",
      "平坝区",
      "普定县",
      "镇宁布依族苗族自治县",
      "关岭布依族苗族自治县",
      "紫云苗族布依族自治县",
    ],
  },
  {
    name: "毕节市",
    counties: [
      "七星关区",
      "大方县",
      "金沙县",
      "织金县",
      "纳雍县",
      "威宁彝族回族苗族自治县",
      "赫章县",
      "黔西市",
    ],
  },
  {
    name: "铜仁市",
    counties: [
      "碧江区",
      "万山区",
      "江口县",
      "玉屏侗族自治县",
      "石阡县",
      "思南县",
      "印江土家族苗族自治县",
      "德江县",
      "沿河土家族自治县",
      "松桃苗族自治县",
    ],
  },
  {
    name: "黔西南布依族苗族自治州",
    counties: [
      "兴义市",
      "兴仁市",
      "普安县",
      "晴隆县",
      "贞丰县",
      "望谟县",
      "册亨县",
      "安龙县",
    ],
  },
  {
    name: "黔东南苗族侗族自治州",
    counties: [
      "凯里市",
      "黄平县",
      "施秉县",
      "三穗县",
      "镇远县",
      "岑巩县",
      "天柱县",
      "锦屏县",
      "剑河县",
      "台江县",
      "黎平县",
      "榕江县",
      "从江县",
      "雷山县",
      "麻江县",
      "丹寨县",
    ],
  },
  {
    name: "黔南布依族苗族自治州",
    counties: [
      "都匀市",
      "福泉市",
      "荔波县",
      "贵定县",
      "瓮安县",
      "独山县",
      "平塘县",
      "罗甸县",
      "长顺县",
      "龙里县",
      "惠水县",
      "三都水族自治县",
    ],
  },
];

/** 贵州省全部分县市（88个）flat 列表 */
export const GUIZHOU_ALL_COUNTIES: string[] = GUIZHOU_REGION.flatMap(
  (c) => c.counties,
);

/** 贵州省全部分市州名称 */
export const GUIZHOU_ALL_CITIES: string[] = GUIZHOU_REGION.map((c) => c.name);

/** 根据市州名称获取下属县区列表 */
export function getCountiesByCity(cityName: string): string[] {
  const city = GUIZHOU_REGION.find((c) => c.name === cityName);
  return city ? city.counties : [];
}

/** 默认省份 */
export const DEFAULT_PROVINCE = "贵州省";
