/**
 * 考核评估 API
 */
import request from "./request";

export interface VillageScore {
  village_id: number;
  village_name: string;
  support_unit: string;
  scores: {
    economic: number;
    social: number;
    project_completion: number;
    fund_execution: number;
  };
  total_score: number;
  level: string;
  rank: number;
}

export interface Anomaly {
  type: string;
  level: string;
  village_id?: number;
  village_name?: string;
  project_id?: number;
  project_name?: string;
  message: string;
  detail: string;
}

export interface TrendPrediction {
  metric: string;
  historical: { year: number; value: number }[];
  predicted: { year: number; value: number }[];
  slope: number;
  intercept: number;
}

export interface VillageComparison {
  village_id: number;
  village_name: string;
  per_capita_income: number;
  collective_income: number;
  total_projects: number;
  completed_projects: number;
  project_completion_rate: number;
  total_funds: number;
}

const BASE = "/assessment";

export const assessmentApi = {
  /** 获取帮扶村综合成效评分 */
  async getVillageScores(year?: number) {
    const response = await request.get(`${BASE}/village-scores`, {
      params: { year },
    });
    return response.data as {
      items: VillageScore[];
      total: number;
      year: number;
      weights: Record<string, number>;
    };
  },

  /** 检测数据异常 */
  async getAnomalies() {
    const response = await request.get(`${BASE}/anomalies`);
    return response.data as { items: Anomaly[]; total: number };
  },

  /** 趋势预测 */
  async getTrendPrediction(metric?: string) {
    const response = await request.get(`${BASE}/trend-prediction`, {
      params: { metric },
    });
    return response.data as TrendPrediction;
  },

  /** 多村横向对比 */
  async compareVillages(villageIds: number[]) {
    const response = await request.get(`${BASE}/village-comparison`, {
      params: { village_ids: villageIds.join(",") },
    });
    return response.data as { items: VillageComparison[]; total: number };
  },
};
