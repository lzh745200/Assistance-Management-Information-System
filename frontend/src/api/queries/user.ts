/**
 * 用户查询 API
 */
import request from '../request'

export async function getUsers(params?: any) {
  const response = await request.get('/users', { params })
  return response.data
}

export async function getUserById(id: string) {
  const response = await request.get(`/users/${id}`)
  return response.data
}

export async function getCurrentUser() {
  const response = await request.get('/auth/me')
  return response.data
}
