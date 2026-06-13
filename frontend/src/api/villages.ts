/**
 * 村庄管理 API
 */
import request from "./request";
import type { PaginatedResponse } from "@/types/api";

/** 村庄 */
export interface Village {
  id: number;
  name: string;
  code: string;
  province?: string;
  city?: string;
  district?: string;
  address?: string;
  population?: number;
  households?: number;
  area?: number;
  description?: string;
  longitude?: number;
  latitude?: number;
  status?: string;
  created_at?: string;
}

/** 创建村庄请求 */
export interface CreateVillageRequest {
  name: string;
  code: string;
  province?: string;
  city?: string;
  district?: string;
  address?: string;
  population?: number;
  households?: number;
  area?: number;
  description?: string;
  longitude?: number;
  latitude?: number;
}

/** 更新村庄请求 */
export interface UpdateVillageRequest {
  name?: string;
  province?: string;
  city?: string;
  district?: string;
  address?: string;
  population?: number;
  households?: number;
  area?: number;
  description?: string;
  longitude?: number;
  latitude?: number;
  status?: string;
}

/** 列表查询参数 */
export interface VillageListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
}

const BASE = "/supported-villages";

export const villageApi = {
  /** 获取村庄列表 */
  async list(params?: VillageListParams): Promise<PaginatedResponse<Village>> {
    const response = await request.get(BASE, { params });
    return response.data;
  },

  /** 获取村庄详情 */
  async getById(id: number): Promise<Village> {
    const response = await request.get(`${BASE}/${id}`);
    return response.data;
  },

  /** 创建村庄 */
  async create(
    data: CreateVillageRequest,
  ): Promise<{ id: number; name: string }> {
    const response = await request.post(BASE, data);
    return response.data;
  },

  /** 更新村庄 */
  async update(
    id: number,
    data: UpdateVillageRequest,
  ): Promise<{ message: string }> {
    const response = await request.put(`${BASE}/${id}`, data);
    return response.data;
  },

  /** 删除村庄 */
  async delete(id: number): Promise<{ message: string }> {
    const response = await request.delete(`${BASE}/${id}`);
    return response.data;
  },
};
