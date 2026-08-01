import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('@/api/request', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    isAdmin: true,
    user: { role: 'admin', id: 1, username: 'admin' },
  }),
}))

vi.mock('@/composables/useDesensitize', () => ({
  useDesensitize: () => ({ ds: (v: any) => v }),
}))

vi.mock('@/utils/clipboard', () => ({
  generateRandomPassword: () => 'Test@12345',
}))

import { get, post, put, del, apiRequest } from '@/api/request'
import UserManagement from '@/views/system/UserManagement.vue'

const mockGet = get as ReturnType<typeof vi.fn>
const mockPost = post as ReturnType<typeof vi.fn>
const mockPut = put as ReturnType<typeof vi.fn>
const mockDel = del as ReturnType<typeof vi.fn>
const mockApiRequest = apiRequest as ReturnType<typeof vi.fn>

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
    created_at: '2025-01-01',
  },
  {
    id: 2,
    username: 'viewer',
    full_name: '查看者',
    role: 'viewer',
    data_scope: 'self',
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

describe('UserManagement page render', () => {
  it('renders user table without DOM errors', async () => {
    const onError = vi.fn()
    const origError = console.error
    console.error = (...args: any[]) => {
      if (String(args[0] || '').includes('setAttribute')) onError(args)
      origError(...args)
    }

    const wrapper = mount(UserManagement, {
      global: {
        stubs: {
          RoleManagement: true,
          PermissionAssignmentDrawer: true,
          // el-card 需渲染 header 与默认插槽，否则标题“用户列表”不进入文本
          'el-card': { template: '<div class="el-card"><slot name="header" /><slot /></div>' },
        },
      },
    })
    await flushPromises()

    console.error = origError

    expect(onError).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('用户列表')
    wrapper.unmount()
  })
})
