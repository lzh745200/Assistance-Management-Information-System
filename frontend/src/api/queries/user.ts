/**
 * 用户查询 API
 */
import { get } from '../request'

export async function getUsers(params?: any) {
  return get('/users', params)
}

export async function getUserById(id: string) {
  return get(`/users/${id}`)
}

export async function getCurrentUser() {
  return get('/auth/me')
}
