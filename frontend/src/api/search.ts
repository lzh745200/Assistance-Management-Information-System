/**
 * 全局搜索 API
 */
import request from "./request";

export interface SearchItem {
  id: number;
  type: "village" | "project" | "policy" | "school" | "user";
  title: string;
  subtitle?: string;
  link: string;
}

export interface SearchResponse {
  total: number;
  items: SearchItem[];
}

export async function globalSearch(
  q: string,
  limit = 20,
): Promise<SearchResponse> {
  const res = await request.get<SearchResponse>("/search", {
    params: { q, limit },
  });
  return res.data;
}
