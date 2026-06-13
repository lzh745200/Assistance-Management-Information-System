/**
 * 用户变更操作 API
 */
import request from "../request";

export async function createUser(data: any) {
  const response = await request.post("/users", data);
  return response.data;
}

export async function updateUser(id: string, data: any) {
  const response = await request.put(`/users/${id}`, data);
  return response.data;
}

export async function deleteUser(id: string) {
  const response = await request.delete(`/users/${id}`);
  return response.data;
}

export async function resetPassword(id: string) {
  const response = await request.post(`/users/${id}/reset-password`);
  return response.data;
}
