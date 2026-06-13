/**
 * 待办事项API服务
 * 提供待办事项的增删改查和状态切换
 */

import api from "./request";

const BASE_URL = "/todos";

/** 获取待办列表 */
export function listTodos(params?: {
  completed?: boolean;
  priority?: string;
  page?: number;
  page_size?: number;
}): Promise<any> {
  return api.get(BASE_URL, { params });
}

/** 获取待办详情 */
export function getTodo(id: number): Promise<any> {
  return api.get(`${BASE_URL}/${id}`);
}

/** 创建待办事项 */
export function createTodo(data: {
  title: string;
  description?: string;
  deadline?: string;
  priority?: string;
}): Promise<any> {
  return api.post(BASE_URL, data);
}

/** 更新待办事项 */
export function updateTodo(
  id: number,
  data: {
    title?: string;
    description?: string;
    deadline?: string;
    completed?: boolean;
    priority?: string;
  },
): Promise<any> {
  return api.put(`${BASE_URL}/${id}`, data);
}

/** 删除待办事项 */
export function deleteTodo(id: number): Promise<any> {
  return api.delete(`${BASE_URL}/${id}`);
}

/** 切换完成状态 */
export function toggleTodo(id: number): Promise<any> {
  return api.patch(`${BASE_URL}/${id}/toggle`);
}
