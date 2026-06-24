import { defineStore } from 'pinia'
import { ref } from 'vue'
import { get, post, put, del } from '@/api/request'
import type { ApiResponse } from '@/types/api'
import { AuthStorage } from '@/utils/authStorage'

export interface User {
  id: number
  username: string
  nickname?: string
  email?: string
  phone?: string
  role?: string
  status?: string
  avatar?: string
  is_active?: boolean
  [key: string]: any
}

interface UserListData {
  items: User[]
  total: number
}

export const useUserStore = defineStore('user', () => {
  const userList = ref<User[]>([])
  // 初始化时从 AuthStorage 恢复 currentUser（防止页面刷新后丢失）
  const _initialUser = AuthStorage.getUser()
  const currentUser = ref<User | null>(_initialUser ? (_initialUser as unknown as User) : null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  async function fetchUsers(params?: Record<string, any>) {
    loading.value = true
    error.value = null
    try {
      const res = await get<ApiResponse<UserListData>>('/users', params)
      if (res.code === 200 && res.data) {
        userList.value = res.data.items ?? []
        total.value = res.data.total ?? 0
      }
    } catch (e: any) {
      error.value = e?.response?.data?.message || e?.message || '获取用户列表失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchUser(id: number) {
    loading.value = true
    error.value = null
    try {
      const res = await get<ApiResponse<User>>(`/users/${id}`)
      if (res.code === 200 && res.data) {
        currentUser.value = res.data
        return res.data
      }
    } catch (e: any) {
      error.value = e?.response?.data?.message || e?.message || '获取用户详情失败'
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: Partial<User>) {
    const res = await post<ApiResponse<User>>('/users', data)
    if (res.code === 200 && res.data) {
      userList.value.unshift(res.data)
      total.value++
    }
    return res
  }

  async function updateUser(id: number, data: Partial<User>) {
    const res = await put<ApiResponse<User>>(`/users/${id}`, data)
    if (res.code === 200 && res.data) {
      const idx = userList.value.findIndex((u) => u.id === id)
      if (idx !== -1) userList.value[idx] = res.data!
      if (currentUser.value?.id === id) currentUser.value = res.data
    }
    return res
  }

  async function deleteUser(id: number) {
    const res = await del<ApiResponse<null>>(`/users/${id}`)
    if (res.code === 200) {
      userList.value = userList.value.filter((u) => u.id !== id)
      total.value--
      if (currentUser.value?.id === id) currentUser.value = null
    }
    return res
  }

  async function resetUserPassword(userId: number, newPassword: string) {
    return post<ApiResponse<null>>(`/users/${userId}/admin-reset-password`, {
      new_password: newPassword,
    })
  }

  async function changePassword(oldPassword: string, newPassword: string) {
    if (!currentUser.value?.id) throw new Error('无法获取用户信息，请重新登录')
    return put(`/users/${currentUser.value.id}/password`, {
      old_password: oldPassword,
      new_password: newPassword,
    })
  }

  async function assignRole(userId: number, roleId: number) {
    return post<ApiResponse<null>>(`/user-management/${userId}/assign-role`, {
      role_id: roleId,
    })
  }

  // Profile / Auth 兼容方法
  async function logout() {
    AuthStorage.clear()
  }

  /** 获取当前用户 ID（从 token 解析或 currentUser） */
  function _getCurrentUserId(): number | null {
    if (currentUser.value?.id) return currentUser.value.id
    try {
      const token = AuthStorage.getToken()
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]))
        // JWT payload 中 sub 是 username（字符串），不是 user_id
        // 优先取 user_id 字段（部分 token 可能包含），没有则返回 null
        const userId = payload?.user_id
        if (typeof userId === 'number') return userId
        return null
      }
    } catch {
      /* ignore */
    }
    return null
  }

  async function getUserProfile(_userId?: number) {
    // 使用 /me 端点（无需传用户 ID，后端从 token 解析）
    const res = await get<ApiResponse<User>>('/users/me')
    if (res.code === 200 && res.data) {
      currentUser.value = res.data as User
      return res.data as User
    }
    // fallback via fetchUser for callers that pass explicit userId
    if (_userId) return fetchUser(_userId)
    throw new Error('无法获取用户信息')
  }

  async function updateUserProfile(data: Partial<User>, _userId?: number) {
    // 使用 /me/profile 端点
    const res = await put<ApiResponse<User>>('/users/me/profile', data)
    if (res.code === 200) {
      if (res.data) currentUser.value = res.data as User
      return res.data || res
    }
    throw new Error('更新失败')
  }

  async function uploadAvatar(file: File, userId?: number) {
    const id = userId || _getCurrentUserId()
    if (!id) throw new Error('无法获取用户ID，请重新登录')
    const formData = new FormData()
    formData.append('avatar', file)
    const res = await post<ApiResponse<{ avatar_url?: string; url?: string }>>(
      `/users/${id}/avatar`,
      formData
    )
    return res.data || (res as any)
  }

  return {
    userList,
    currentUser,
    loading,
    error,
    total,
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    resetUserPassword,
    changePassword,
    assignRole,
    logout,
    getUserProfile,
    updateUserProfile,
    uploadAvatar,
  }
})
