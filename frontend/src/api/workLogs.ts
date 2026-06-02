/**
 * 工作日志 API
 */
import request from "./request";

export interface WorkLog {
  id: number;
  title: string;
  content?: string;
  log_type: string;
  log_date: string;
  work_date?: string; // 兼容旧字段
  start_time?: string;
  end_time?: string;
  location?: string;
  participants?: string;
  related_project_id?: number;
  related_village_id?: number;
  project_id?: number;
  village_id?: number;
  school_id?: number;
  category?: string;
  tags?: string;
  created_by?: number;
  user_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface WorkLogListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  log_type?: string;
  category?: string;
  source?: "auto" | "manual"; // 日志来源筛选
  start_date?: string;
  end_date?: string;
  project_id?: number;
  village_id?: number;
}

const BASE = "/work-logs";

export const workLogApi = {
  /** 获取工作日志列表 */
  async list(params?: WorkLogListParams) {
    const response = await request.get(BASE, { params });
    return response.data as {
      items: WorkLog[];
      total: number;
      page: number;
      page_size: number;
    };
  },

  /** 获取单条 */
  async getById(id: number) {
    const response = await request.get(`${BASE}/${id}`);
    return response.data as WorkLog;
  },

  /** 创建 */
  async create(data: Partial<WorkLog>) {
    // 确保传递后端期望的 log_date 字段
    const payload: Record<string, unknown> = { ...data };
    if (!payload.log_date && payload.work_date) {
      payload.log_date = payload.work_date;
    }
    if (!payload.log_date) {
      payload.log_date = new Date().toISOString().split("T")[0];
    }
    const response = await request.post(BASE, payload);
    return response.data as WorkLog;
  },

  /** 更新 */
  async update(id: number, data: Partial<WorkLog>) {
    const response = await request.put(`${BASE}/${id}`, data);
    return response.data as WorkLog;
  },

  /** 删除 */
  async delete(id: number) {
    const response = await request.delete(`${BASE}/${id}`);
    return response.data;
  },

  /** 日历视图数据 */
  async getCalendarView(
    year: number,
    month: number,
    source?: "auto" | "manual",
  ) {
    const params: Record<string, any> = { year, month };
    if (source) params.source = source;
    const response = await request.get(`${BASE}/calendar`, { params });
    return response.data as { items: WorkLog[]; year: number; month: number };
  },
};
