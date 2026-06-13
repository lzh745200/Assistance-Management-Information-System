/**
 * 数据质量管理API服务
 * 提供数据验证、清洗、去重和质量报告功能
 */

import api from "./request";

const BASE_URL = "/data-quality";

/** 验证数据 */
export function validate(data: {
  entity_type: string;
  data: Record<string, any>;
  field_name?: string;
}): Promise<any> {
  return api.post(`${BASE_URL}/validate`, data);
}

/** 清洗数据（需要管理员权限） */
export function clean(data: {
  records: any[];
  cleaning_rules: Record<string, any>;
}): Promise<any> {
  return api.post(`${BASE_URL}/clean`, data);
}

/** 数据去重 */
export function deduplicate(
  records: any[],
  keyFields: string[],
  similarityThreshold?: number,
): Promise<any> {
  return api.post(`${BASE_URL}/deduplicate`, records, {
    params: {
      key_fields: keyFields,
      similarity_threshold: similarityThreshold ?? 0.9,
    },
  });
}

/** 获取数据质量综合报告 */
export function getReport(): Promise<any> {
  return api.get(`${BASE_URL}/report`);
}

/** 全面数据质量检查 */
export function runFullCheck(): Promise<any> {
  return api.post(`${BASE_URL}/full-check`);
}
