/**
 * 用户变更操作 API
 */
import { post, put, del } from '../request'

export async function createUser(data: any) {
  return post('/users', data)
}

export async function updateUser(id: string, data: any) {
  return put(`/users/${id}`, data)
}

export async function deleteUser(id: string) {
  return del(`/users/${id}`)
}

export async function resetPassword(id: string, newPassword?: string) {
  return post(`/users/${id}/admin-reset-password`, {
    new_password: newPassword,
  })
}
