import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { setActivePinia, createPinia } from 'pinia'

const userRef = ref<any>(null)
const authState = {
  get user() {
    return userRef.value
  },
}

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authState,
}))

import { useDesensitize } from '@/composables/useDesensitize'

describe('useDesensitize', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    userRef.value = null
  })

  it('用户未登录时 role 默认 viewer', () => {
    const { role } = useDesensitize()
    expect(role.value).toBe('viewer')
  })

  it('role 反映当前用户角色', () => {
    userRef.value = { id: 1, username: 'admin', role: 'admin' }
    const { role } = useDesensitize()
    expect(role.value).toBe('admin')
  })

  it('ds() 以当前角色对手机号脱敏（admin 角色返回原文）', () => {
    userRef.value = { id: 1, username: 'admin', role: 'admin' }
    const { ds } = useDesensitize()
    expect(ds('13812345678', 'phone')).toBe('13812345678')
  })

  it('ds() 以 viewer 角色完全隐藏手机号', () => {
    userRef.value = { id: 1, username: 'v', role: 'viewer' }
    const { ds } = useDesensitize()
    expect(ds('13812345678', 'phone')).toBe('****')
  })

  it('ds() 支持 idCard 类型且按角色处理', () => {
    userRef.value = { id: 1, username: 'u', role: 'user' }
    const { ds } = useDesensitize()
    const result = ds('110101199003071234', 'idCard')
    expect(result).toContain('****')
  })

  it('暴露全部基础脱敏工具函数', () => {
    const c = useDesensitize()
    for (const key of [
      'maskPhone',
      'maskIdCard',
      'maskName',
      'maskBankCard',
      'maskEmail',
      'maskAddress',
      'maskAmount',
      'autoDesensitize',
    ]) {
      expect(typeof (c as any)[key]).toBe('function')
    }
  })
})
