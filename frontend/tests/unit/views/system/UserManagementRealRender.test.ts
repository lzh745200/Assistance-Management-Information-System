/**
 * UserManagement 真实 Element Plus 渲染复现测试
 * 目标：复现生产环境 "Failed to execute 'setAttribute' on 'Element': '0' is not a valid attribute name"
 * 方法：mount 时对 el-* 组件使用 stub: false（真实渲染），复现真实 DOM patch 路径
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const { authState, mockGet, mockPost, mockPut, mockDel, mockApiRequest } = vi.hoisted(() => ({
  authState: { isAdmin: true, user: { role: 'admin', id: 1 } },
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDel: vi.fn(),
  mockApiRequest: vi.fn(),
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  put: mockPut,
  del: mockDel,
  apiRequest: mockApiRequest,
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authState,
}))

vi.mock('@/composables/useDesensitize', () => ({
  useDesensitize: () => ({ ds: (v: any) => v }),
}))

vi.mock('@/utils/clipboard', () => ({
  generateRandomPassword: () => 'Test@12345',
}))

import UserManagement from '@/views/system/UserManagement.vue'

const users = [
  {
    id: 1,
    username: 'admin',
    full_name: '管理员',
    role: 'admin',
    data_scope: 'all',
    department: '综合部',
    phone: '13800000000',
    email: 'a@b.com',
    is_active: true,
    last_login: '2026-01-01',
    organization_name: '市局',
    machine_code: 'ABC123',
  },
  {
    id: 2,
    username: 'zhangsan',
    full_name: '张三',
    role: 'user',
    data_scope: 'org',
    department: '',
    phone: '',
    email: '',
    is_active: false,
    last_login: null,
    organization_name: null,
    machine_code: null,
  },
]

beforeEach(() => {
  vi.clearAllMocks()
  mockApiRequest.mockResolvedValue({ items: users, total: 2 })
  mockGet.mockImplementation((url: string) => {
    if (url === '/users/pending/list') return Promise.resolve({ data: [] })
    if (url === '/rbac/roles') return Promise.resolve({ data: { items: [] } })
    if (url === '/organizations/tree') return Promise.resolve({ data: [] })
    return Promise.resolve({ data: {} })
  })
  mockPost.mockResolvedValue({ data: {} })
  mockPut.mockResolvedValue({ data: {} })
  mockDel.mockResolvedValue({ data: {} })
})

describe('UserManagement real Element Plus render', () => {
  it('renders without InvalidCharacterError (setAttribute "0")', async () => {
    const errors: string[] = []
    const origError = console.error
    console.error = (...args: any[]) => {
      const msg = String(args[0] || '')
      if (msg.includes('setAttribute') || msg.includes('InvalidCharacterError')) {
        errors.push(msg)
      }
      origError(...args)
    }

    let wrapper: any
    try {
      wrapper = mount(UserManagement, {
        global: {
          // 真实渲染 Element Plus 组件（关闭全局 stub）
          stubs: {
            RoleManagement: true,
            PermissionAssignmentDrawer: true,
            'el-table': false,
            'el-table-column': false,
            'el-tabs': false,
            'el-tab-pane': false,
            'el-select': false,
            'el-option': false,
            'el-option-group': false,
            'el-pagination': false,
            'el-tag': false,
            'el-badge': false,
            'el-button': false,
            'el-form': false,
            'el-form-item': false,
            'el-input': false,
            'el-card': false,
            'el-dialog': false,
            'el-tree-select': false,
            'el-switch': false,
            'el-dropdown': false,
            'el-dropdown-menu': false,
            'el-dropdown-item': false,
            'el-icon': false,
            'el-divider': false,
            'el-empty': false,
            'el-alert': false,
          },
        },
      })
      await flushPromises()
      await new Promise((r) => setTimeout(r, 100))
      await flushPromises()
    } catch (e: any) {
      errors.push(`MOUNT_ERROR: ${e?.message || e}`)
    } finally {
      console.error = origError
      wrapper?.unmount()
    }

    expect(errors).toEqual([])
  })
})
