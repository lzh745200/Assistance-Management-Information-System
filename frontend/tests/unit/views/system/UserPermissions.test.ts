/**
 * views/system/UserPermissions.vue 覆盖率攻坚
 * 覆盖：组织树懒加载六分支、节点点击/刷新树、Tab 切换按需加载、
 * 组织用户 CRUD、角色分配（getRoleTagType 全映射、移除角色确认流）、
 * 权限授予/撤销，以及模板 v-if/v-else、v-model 内联处理器、
 * el-table-column 样本行、el-tag close、el-popconfirm confirm 交互。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// vi.mock 工厂会被提升到模块顶部注册，直接引用下方 const 会触发 TDZ；
// 所有被工厂引用的对象放入 vi.hoisted 中先行初始化。
const {
  ElMessage,
  confirmMock,
  apiGetOrgTree,
  apiGetOrgUsers,
  apiAssignOrg,
  apiRemoveOrg,
  apiGetUserRoles,
  apiAssignRole,
  apiRemoveRole,
  apiGetUserPerms,
  apiGrantPerm,
  apiRevokePerm,
  mockListUsers,
  normalizeMock,
  rootLoadDataMock,
} = vi.hoisted(() => {
  return {
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    confirmMock: vi.fn(),
    apiGetOrgTree: vi.fn(),
    apiGetOrgUsers: vi.fn(),
    apiAssignOrg: vi.fn(),
    apiRemoveOrg: vi.fn(),
    apiGetUserRoles: vi.fn(),
    apiAssignRole: vi.fn(),
    apiRemoveRole: vi.fn(),
    apiGetUserPerms: vi.fn(),
    apiGrantPerm: vi.fn(),
    apiRevokePerm: vi.fn(),
    mockListUsers: vi.fn(),
    normalizeMock: vi.fn(),
    rootLoadDataMock: vi.fn(),
  }
})

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: confirmMock },
}))

// refreshTree 用 nextTick 回调读取 treeRef；真实 nextTick 会等重渲染先把模板 ref
// 重同步回 stub 实例，导致 treeRef 为空的兜底分支不可测。这里让带回调的 nextTick
// 同步执行回调（无参调用仍走真实实现，保证测试中的 await nextTick() 正常冲刷）。
vi.mock('vue', async (importOriginal) => {
  const actual = await importOriginal<any>()
  return {
    ...actual,
    nextTick: (cb?: () => void) => (cb ? (cb(), Promise.resolve()) : actual.nextTick()),
  }
})

vi.mock('@/api/userPermissions', () => ({
  userPermissionsApi: {
    getOrganizationTree: apiGetOrgTree,
    getOrganizationUsers: apiGetOrgUsers,
    assignOrganization: apiAssignOrg,
    removeOrganization: apiRemoveOrg,
    getUserRoles: apiGetUserRoles,
    assignRole: apiAssignRole,
    removeRole: apiRemoveRole,
    getUserPermissions: apiGetUserPerms,
    grantPermission: apiGrantPerm,
    revokePermission: apiRevokePerm,
  },
}))

vi.mock('@/api/userManagement', () => ({
  listUsers: mockListUsers,
}))

vi.mock('@/utils/treeNormalizer', () => ({
  normalizeTreeNodes: normalizeMock,
}))

import UserPermissions from '@/views/system/UserPermissions.vue'

function mountComp() {
  // setup.ts 的全局 el-* stub 默认不渲染插槽，需 renderStubDefaultSlot；
  // 具名插槽（header/footer）与作用域插槽（表格行、树节点）需自定义 stub。
  return mount(UserPermissions, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-card': {
          name: 'ElCard',
          template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
        },
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        // el-tree 需携带 store/root 供 refreshTree 内部 nextTick 回调访问；
        // 作用域插槽注入样本节点覆盖树节点模板。
        'el-tree': {
          name: 'ElTree',
          template: '<div class="el-tree-stub"><slot :data="sampleNode" /></div>',
          emits: ['node-click'],
          data() {
            return {
              sampleNode: { name: '样本节点' },
              store: { nodesMap: {} },
              root: { childNodes: [{}], loadData: rootLoadDataMock },
            }
          },
        },
        // 注入两行样本数据，覆盖 org_role 空值兜底、is_primary 真/假等模板两侧分支
        'el-table-column': {
          name: 'ElTableColumn',
          template: '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /></div>',
          data() {
            return {
              rowA: { user_id: 11, username: 'zhangsan', org_role: 'admin', is_primary: true },
              rowB: { user_id: 12, username: 'lisi', org_role: '', is_primary: false },
            }
          },
        },
      },
    },
  })
}

const orgA = { id: 7, name: '组织A' }

/** 通过 ElTree 的 node-click 事件选中组织（真实交互路径） */
async function selectOrg(wrapper: any, org: any = orgA) {
  wrapper.findComponent({ name: 'ElTree' }).vm.$emit('node-click', org)
  await flushPromises()
  await nextTick()
}

const roleUsers = [
  {
    user_id: 1,
    username: 'u1',
    org_role: 'member',
    is_primary: false,
    roles: [
      { id: 1, name: 'super_admin' },
      { role_id: 'manager' },
      { role_id: 'approval_leader', name: '审批负责人' },
      { id: 2 },
      'viewer',
    ],
    permissions: [],
  },
  { user_id: 2, username: 'u2', org_role: 'member', is_primary: false, roles: [], permissions: [] },
  { user_id: 3, username: 'u3', org_role: 'member', is_primary: false, roles: null, permissions: null },
]

const permUsers = [
  { user_id: 1, username: 'u1', org_role: 'member', is_primary: false, roles: [], permissions: ['user:read', 'project:write'] },
  { user_id: 2, username: 'u2', org_role: 'member', is_primary: false, roles: [], permissions: [] },
  { user_id: 3, username: 'u3', org_role: 'member', is_primary: false, roles: [], permissions: null },
]

beforeEach(() => {
  vi.resetAllMocks()
  apiGetOrgTree.mockResolvedValue({ success: true, data: [{ id: 1, name: '总部' }] })
  apiGetOrgUsers.mockResolvedValue({
    success: true,
    data: [{ user_id: 1, username: 'u1', role: 'admin', is_primary: true }],
  })
  apiAssignOrg.mockResolvedValue({ success: true })
  apiRemoveOrg.mockResolvedValue({ success: true })
  apiGetUserRoles.mockResolvedValue({ success: true, data: [] })
  apiAssignRole.mockResolvedValue({ success: true })
  apiRemoveRole.mockResolvedValue({ success: true })
  apiGetUserPerms.mockResolvedValue({ success: true, data: [] })
  apiGrantPerm.mockResolvedValue({ success: true })
  apiRevokePerm.mockResolvedValue({ success: true })
  mockListUsers.mockResolvedValue({
    success: true,
    data: { items: [{ id: 1, username: 'u1', name: '张三' }, { id: 2, username: 'u2' }] },
  })
  normalizeMock.mockImplementation((nodes: any) => nodes)
  confirmMock.mockResolvedValue(undefined)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('挂载与组织树懒加载', () => {
  it('挂载：默认展示未选择提示与树空态', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.selectedOrgId).toBeNull()
    expect(wrapper.find('.no-selection').exists()).toBe(true)
    expect(wrapper.find('.org-header').exists()).toBe(false)
    expect(wrapper.find('.no-selection el-empty-stub').attributes('description')).toBe('请在左侧选择组织机构')
    expect(wrapper.find('.tree-container el-empty-stub').attributes('description')).toBe('暂无组织机构数据')
  })

  it('loadNode 根级别：成功数组 → resolve 规范化数据并复位 loading', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resolve = vi.fn()
    const rows = [{ id: 1, name: '总部' }]
    apiGetOrgTree.mockResolvedValueOnce({ success: true, data: rows })
    vm.loadNode({ level: 0 }, resolve)
    expect(vm.treeLoading).toBe(true)
    await flushPromises()
    expect(apiGetOrgTree).toHaveBeenCalledTimes(1)
    expect(normalizeMock).toHaveBeenCalledWith(rows)
    expect(resolve).toHaveBeenCalledWith(rows)
    expect(vm.treeLoading).toBe(false)
  })

  it('loadNode 根级别：success=false 与 data 非数组 → resolve([])', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const r1 = vi.fn()
    apiGetOrgTree.mockResolvedValueOnce({ success: false, data: [{ id: 1 }] })
    vm.loadNode({ level: 0 }, r1)
    await flushPromises()
    expect(r1).toHaveBeenCalledWith([])
    const r2 = vi.fn()
    apiGetOrgTree.mockResolvedValueOnce({ success: true, data: { not: 'array' } })
    vm.loadNode({ level: 0 }, r2)
    await flushPromises()
    expect(r2).toHaveBeenCalledWith([])
  })

  it('loadNode 根级别：请求异常 → 错误提示并 resolve([])', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resolve = vi.fn()
    apiGetOrgTree.mockRejectedValueOnce(new Error('net'))
    vm.loadNode({ level: 0 }, resolve)
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('加载组织树失败')
    expect(resolve).toHaveBeenCalledWith([])
    expect(vm.treeLoading).toBe(false)
  })

  it('loadNode 子节点：成功数组 → 按父节点 id 加载并 resolve', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resolve = vi.fn()
    const rows = [{ id: 8, name: '下级' }]
    apiGetOrgTree.mockResolvedValueOnce({ success: true, data: rows })
    vm.loadNode({ level: 1, data: { id: 5 } }, resolve)
    await flushPromises()
    expect(apiGetOrgTree).toHaveBeenCalledWith(5)
    expect(resolve).toHaveBeenCalledWith(rows)
  })

  it('loadNode 子节点：success=false → resolve([])', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resolve = vi.fn()
    apiGetOrgTree.mockResolvedValueOnce({ success: false, data: null })
    vm.loadNode({ level: 1, data: { id: 5 } }, resolve)
    await flushPromises()
    expect(resolve).toHaveBeenCalledWith([])
  })

  it('loadNode 子节点：请求异常 → 错误提示并 resolve([])', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const resolve = vi.fn()
    apiGetOrgTree.mockRejectedValueOnce(new Error('net'))
    vm.loadNode({ level: 1, data: { id: 5 } }, resolve)
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('加载子组织失败')
    expect(resolve).toHaveBeenCalledWith([])
  })
})

describe('树节点交互与刷新', () => {
  it('node-click：选中组织、切回组织分配 Tab 并加载用户', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.activeTab = 'role-assign'
    await selectOrg(wrapper)
    expect(vm.selectedOrg).toEqual(orgA)
    expect(vm.selectedOrgId).toBe(7)
    expect(vm.activeTab).toBe('org-assign')
    expect(apiGetOrgUsers).toHaveBeenCalledWith(7, false)
    expect(wrapper.find('.org-header').exists()).toBe(true)
    expect(wrapper.find('.org-name').text()).toBe('组织A')
    expect(wrapper.find('.no-selection').exists()).toBe(false)
  })

  it('组织无名称与 selectedOrg 为空 → 显示「未命名组织」兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper, { id: 8 })
    expect(wrapper.find('.org-name').text()).toBe('未命名组织')
    vm.selectedOrg = null
    await nextTick()
    expect(wrapper.find('.org-name').text()).toBe('未命名组织')
  })

  it('refreshTree：treeRef 存在 → 清空数据并触发 root.loadData', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    // 通过头部刷新按钮点击覆盖模板 @click 绑定
    await wrapper.find('.card-header el-button-stub').trigger('click')
    await flushPromises()
    await nextTick()
    expect(vm.treeData).toEqual([])
    expect(vm.selectedOrgId).toBeNull()
    expect(vm.selectedOrg).toBeNull()
    expect(rootLoadDataMock).toHaveBeenCalled()
  })

  it('refreshTree：treeRef 为空 → 安全跳过 loadData', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.treeRef = null
    vm.refreshTree()
    await flushPromises()
    await nextTick()
    expect(rootLoadDataMock).not.toHaveBeenCalled()
  })

  it('树空态 v-if 两侧：treeLoading 中与 treeData 非空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(wrapper.find('.tree-container el-empty-stub').exists()).toBe(true)
    vm.treeLoading = true
    await nextTick()
    expect(wrapper.find('.tree-container el-empty-stub').exists()).toBe(false)
    vm.treeLoading = false
    vm.treeData = [{ id: 1, name: '总部' }]
    await nextTick()
    expect(wrapper.find('.tree-container el-empty-stub').exists()).toBe(false)
  })
})

describe('Tab 切换按需加载', () => {
  it('未选组织：handleTabChange 直接返回，不发请求', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 未选组织时 el-tabs 不渲染（v-else 分支），直接调用处理器（模板为直接引用绑定）
    vm.handleTabChange('role-assign')
    await flushPromises()
    expect(apiGetOrgUsers).not.toHaveBeenCalled()
  })

  it('v-model 更新 activeTab；org-assign → 加载组织用户', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    const tabs = wrapper.findComponent({ name: 'ElTabs' })
    tabs.vm.$emit('update:modelValue', 'org-assign')
    expect(vm.activeTab).toBe('org-assign')
    apiGetOrgUsers.mockClear()
    tabs.vm.$emit('tab-change', 'org-assign')
    await flushPromises()
    expect(apiGetOrgUsers).toHaveBeenCalledWith(7, false)
  })

  it('role-assign → 加载用户角色', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await selectOrg(wrapper)
    apiGetUserRoles.mockClear()
    wrapper.findComponent({ name: 'ElTabs' }).vm.$emit('tab-change', 'role-assign')
    await flushPromises()
    expect(apiGetUserRoles).toHaveBeenCalledWith(1)
  })

  it('perm-grant → 加载用户权限', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await selectOrg(wrapper)
    apiGetUserPerms.mockClear()
    wrapper.findComponent({ name: 'ElTabs' }).vm.$emit('tab-change', 'perm-grant')
    await flushPromises()
    expect(apiGetUserPerms).toHaveBeenCalledWith(1)
  })

  it('未知 Tab 名称 → 不触发任何加载', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await selectOrg(wrapper)
    apiGetOrgUsers.mockClear()
    apiGetUserRoles.mockClear()
    apiGetUserPerms.mockClear()
    wrapper.findComponent({ name: 'ElTabs' }).vm.$emit('tab-change', 'unknown-tab')
    await flushPromises()
    expect(apiGetOrgUsers).not.toHaveBeenCalled()
    expect(apiGetUserRoles).not.toHaveBeenCalled()
    expect(apiGetUserPerms).not.toHaveBeenCalled()
  })
})

describe('组织用户加载（Tab 1）', () => {
  it('loadOrgUsers：未选组织 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.loadOrgUsers()
    expect(apiGetOrgUsers).not.toHaveBeenCalled()
  })

  it('loadOrgUsers：字段多级兜底映射（user_id/id、role/org_role/member、username 空）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    apiGetOrgUsers.mockResolvedValueOnce({
      success: true,
      data: [
        { user_id: 1, username: 'a', role: 'admin', is_primary: 1 },
        { id: 2, username: 'b', org_role: 'viewer' },
        { id: 3 },
      ],
    })
    await vm.loadOrgUsers()
    expect(vm.orgUsers).toEqual([
      { user_id: 1, username: 'a', org_role: 'admin', is_primary: true, roles: [], permissions: [] },
      { user_id: 2, username: 'b', org_role: 'viewer', is_primary: false, roles: [], permissions: [] },
      { user_id: 3, username: '', org_role: 'member', is_primary: false, roles: [], permissions: [] },
    ])
    expect(vm.userCount).toBe(3)
    expect(vm.usersLoading).toBe(false)
  })

  it('loadOrgUsers：success=false 与 data 非数组 → 置空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    apiGetOrgUsers.mockResolvedValueOnce({ success: false, data: [] })
    await vm.loadOrgUsers()
    expect(vm.orgUsers).toEqual([])
    apiGetOrgUsers.mockResolvedValueOnce({ success: true, data: { not: 'array' } })
    await vm.loadOrgUsers()
    expect(vm.orgUsers).toEqual([])
  })

  it('loadOrgUsers：请求异常 → 错误提示并置空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    apiGetOrgUsers.mockRejectedValueOnce(new Error('net'))
    await vm.loadOrgUsers()
    expect(ElMessage.error).toHaveBeenCalledWith('加载组织用户失败')
    expect(vm.orgUsers).toEqual([])
    expect(vm.usersLoading).toBe(false)
  })

  it('表格样本行渲染 + popconfirm 移除用户成功/失败/未选组织三分支', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    // 未选组织：直接返回
    await vm.handleRemoveUser({ user_id: 99 })
    expect(apiRemoveOrg).not.toHaveBeenCalled()
    await selectOrg(wrapper)
    // 样本行模板分支：org_role 空值兜底 member、is_primary 是/否
    expect(wrapper.text()).toContain('member')
    expect(wrapper.text()).toContain('是')
    expect(wrapper.text()).toContain('否')
    // popconfirm confirm 真实交互（rowA → user_id 11）
    const confirms = wrapper.findAllComponents({ name: 'ElPopconfirm' })
    expect(confirms.length).toBe(2)
    confirms[0].vm.$emit('confirm')
    await flushPromises()
    expect(apiRemoveOrg).toHaveBeenCalledWith(11, 7)
    expect(ElMessage.success).toHaveBeenCalledWith('用户已从组织中移除')
    // 失败分支（rowB → user_id 12）
    apiRemoveOrg.mockRejectedValueOnce(new Error('net'))
    confirms[1].vm.$emit('confirm')
    await flushPromises()
    expect(apiRemoveOrg).toHaveBeenCalledWith(12, 7)
    expect(ElMessage.error).toHaveBeenCalledWith('移除用户失败')
  })
})

describe('添加用户对话框', () => {
  it('openAddUserDialog：重置表单、加载用户列表；再次打开不重复加载', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addUserForm.user_id = 5
    vm.addUserForm.role = 'admin'
    vm.addUserForm.is_primary = true
    await vm.openAddUserDialog()
    expect(vm.addUserForm).toEqual({ user_id: null, role: 'member', is_primary: false })
    expect(vm.addUserDialogVisible).toBe(true)
    expect(mockListUsers).toHaveBeenCalledWith({ page_size: 200 })
    expect(vm.allUsers).toHaveLength(2)
    expect(vm.allUsersLoading).toBe(false)
    await vm.openAddUserDialog()
    expect(mockListUsers).toHaveBeenCalledTimes(1)
  })

  it('通过「添加用户」按钮点击打开对话框', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes('添加用户'))
    expect(btn).toBeDefined()
    await btn!.trigger('click')
    await flushPromises()
    expect(vm.addUserDialogVisible).toBe(true)
    expect(mockListUsers).toHaveBeenCalled()
  })

  it('openAddUserDialog：响应无 items 或 success=false → 用户列表保持空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    mockListUsers.mockResolvedValueOnce({ success: true, data: {} })
    await vm.openAddUserDialog()
    expect(vm.allUsers).toEqual([])
    mockListUsers.mockResolvedValueOnce({ success: false, data: null })
    await vm.openAddUserDialog()
    expect(vm.allUsers).toEqual([])
  })

  it('openAddUserDialog：请求异常 → 错误提示', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    mockListUsers.mockRejectedValueOnce(new Error('net'))
    await vm.openAddUserDialog()
    expect(ElMessage.error).toHaveBeenCalledWith('加载用户列表失败')
    expect(vm.allUsersLoading).toBe(false)
  })

  it('handleAddUserSubmit：formRef 为空 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.addUserFormRef = undefined
    await vm.handleAddUserSubmit()
    expect(apiAssignOrg).not.toHaveBeenCalled()
  })

  it('handleAddUserSubmit：校验未通过 → 不发请求', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addUserForm.user_id = 5
    vm.addUserFormRef = { validate: (cb: any) => cb(false) }
    await vm.handleAddUserSubmit()
    await flushPromises()
    expect(apiAssignOrg).not.toHaveBeenCalled()
  })

  it('handleAddUserSubmit：缺 user_id 或缺组织 → 校验通过也不发请求', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addUserForm.user_id = null
    vm.addUserFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddUserSubmit()
    await flushPromises()
    expect(apiAssignOrg).not.toHaveBeenCalled()
    vm.selectedOrgId = null
    vm.addUserForm.user_id = 5
    vm.addUserFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddUserSubmit()
    await flushPromises()
    expect(apiAssignOrg).not.toHaveBeenCalled()
  })

  it('handleAddUserSubmit 成功：提交分配、关闭对话框并刷新列表', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addUserForm.user_id = 5
    vm.addUserForm.role = 'admin'
    vm.addUserForm.is_primary = true
    vm.addUserDialogVisible = true
    apiGetOrgUsers.mockClear()
    vm.addUserFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddUserSubmit()
    await flushPromises()
    expect(apiAssignOrg).toHaveBeenCalledWith({
      user_id: 5,
      organization_id: 7,
      role: 'admin',
      is_primary: true,
    })
    expect(ElMessage.success).toHaveBeenCalledWith('用户已添加到组织')
    expect(vm.addUserDialogVisible).toBe(false)
    expect(apiGetOrgUsers).toHaveBeenCalled()
    expect(vm.addUserSubmitting).toBe(false)
  })

  it('handleAddUserSubmit 失败 → 错误提示且提交态复位', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addUserForm.user_id = 5
    apiAssignOrg.mockRejectedValueOnce(new Error('net'))
    vm.addUserFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddUserSubmit()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('添加用户失败')
    expect(vm.addUserSubmitting).toBe(false)
  })

  it('对话框 v-model 与取消按钮：addUser 弹窗及各表单项 update 处理器', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    const dialogs = wrapper.findAllComponents({ name: 'ElDialog' })
    expect(dialogs.length).toBe(3)
    // v-model 内联赋值处理器
    dialogs[0].vm.$emit('update:modelValue', true)
    expect(vm.addUserDialogVisible).toBe(true)
    dialogs[1].vm.$emit('update:modelValue', true)
    expect(vm.addRoleDialogVisible).toBe(true)
    dialogs[2].vm.$emit('update:modelValue', true)
    expect(vm.grantPermDialogVisible).toBe(true)
    // 取消按钮内联 @click 赋值
    const cancels = wrapper.findAll('el-button-stub').filter((b) => b.text().trim() === '取消')
    expect(cancels.length).toBe(3)
    await cancels[0].trigger('click')
    expect(vm.addUserDialogVisible).toBe(false)
    await cancels[1].trigger('click')
    expect(vm.addRoleDialogVisible).toBe(false)
    await cancels[2].trigger('click')
    expect(vm.grantPermDialogVisible).toBe(false)
    // 各 v-model 表单项
    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    expect(selects.length).toBe(3)
    selects[0].vm.$emit('update:modelValue', 5)
    expect(vm.addUserForm.user_id).toBe(5)
    selects[1].vm.$emit('update:modelValue', 'admin')
    expect(vm.addUserForm.role).toBe('admin')
    selects[2].vm.$emit('update:modelValue', 'manager')
    expect(vm.addRoleForm.role_id).toBe('manager')
    const sw = wrapper.findComponent({ name: 'ElSwitch' })
    sw.vm.$emit('update:modelValue', true)
    expect(vm.addUserForm.is_primary).toBe(true)
    const inputs = wrapper.findAllComponents({ name: 'ElInput' })
    inputs[0].vm.$emit('update:modelValue', 'x') // 禁用输入框（单向绑定，无处理器）
    inputs[1].vm.$emit('update:modelValue', 'user:read')
    expect(vm.grantPermForm.permission).toBe('user:read')
    const pickers = wrapper.findAllComponents({ name: 'ElDatePicker' })
    expect(pickers.length).toBe(2)
    pickers[0].vm.$emit('update:modelValue', '2025-01-01T00:00:00')
    expect(vm.addRoleForm.expires_at).toBe('2025-01-01T00:00:00')
    pickers[1].vm.$emit('update:modelValue', '2025-02-01T00:00:00')
    expect(vm.grantPermForm.expires_at).toBe('2025-02-01T00:00:00')
  })
})

describe('角色分配（Tab 2）', () => {
  it('loadOrgUsersWithRoles：聚合角色成功；单用户角色失败被忽略；非数组角色保持空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    apiGetOrgUsers.mockResolvedValueOnce({
      success: true,
      data: [
        { user_id: 1, username: 'a', role: 'admin' },
        { id: 2 },
        { user_id: 3, username: 'c' },
      ],
    })
    apiGetUserRoles.mockImplementation((uid: number) => {
      if (uid === 1) return Promise.resolve({ success: true, data: [{ id: 1, name: 'admin' }] })
      if (uid === 2) return Promise.resolve({ success: true, data: { not: 'array' } })
      return Promise.reject(new Error('net'))
    })
    await vm.loadOrgUsersWithRoles()
    expect(vm.orgUsersWithRoles).toHaveLength(3)
    expect(vm.orgUsersWithRoles[0].roles).toEqual([{ id: 1, name: 'admin' }])
    expect(vm.orgUsersWithRoles[1].roles).toEqual([])
    expect(vm.orgUsersWithRoles[2].roles).toEqual([])
    expect(vm.rolesLoading).toBe(false)
  })

  it('loadOrgUsersWithRoles：非数组响应 → 置空；异常 → 提示；未选组织 → 返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.loadOrgUsersWithRoles()
    expect(apiGetOrgUsers).not.toHaveBeenCalled()
    await selectOrg(wrapper)
    apiGetOrgUsers.mockResolvedValueOnce({ success: true, data: { not: 'array' } })
    await vm.loadOrgUsersWithRoles()
    expect(vm.orgUsersWithRoles).toEqual([])
    apiGetOrgUsers.mockRejectedValueOnce(new Error('net'))
    await vm.loadOrgUsersWithRoles()
    expect(ElMessage.error).toHaveBeenCalledWith('加载组织用户失败')
    expect(vm.orgUsersWithRoles).toEqual([])
    expect(vm.rolesLoading).toBe(false)
  })

  it('getRoleTagType 全映射与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.getRoleTagType({ name: 'super_admin' })).toBe('danger')
    expect(vm.getRoleTagType({ name: 'admin' })).toBe('danger')
    expect(vm.getRoleTagType({ role_id: 'manager' })).toBe('warning')
    expect(vm.getRoleTagType({ name: 'approval_leader' })).toBe('success')
    expect(vm.getRoleTagType({ role_id: 'operator' })).toBe('info')
    expect(vm.getRoleTagType({})).toBe('info')
  })

  it('角色卡片渲染各分支 + 「添加角色」按钮打开对话框', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.orgUsersWithRoles = JSON.parse(JSON.stringify(roleUsers))
    await nextTick()
    // v-if 空态消失、角色标签与「暂无角色」并存
    expect(wrapper.text()).toContain('viewer')
    expect(wrapper.text()).toContain('暂无角色')
    expect(wrapper.text()).toContain('审批负责人')
    vm.addRoleForm.role_id = 'dirty'
    vm.addRoleForm.expires_at = 'dirty'
    const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes('添加角色'))
    expect(btn).toBeDefined()
    await btn!.trigger('click')
    expect(vm.addRoleTarget.user_id).toBe(1)
    expect(vm.addRoleForm).toEqual({ role_id: '', expires_at: '' })
    expect(vm.addRoleDialogVisible).toBe(true)
    // 目标用户名渲染
    expect(wrapper.text()).toContain('u1')
  })

  it('handleAddRoleSubmit：formRef 空 / 校验失败 / 无目标 → 均不发请求', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.addRoleFormRef = undefined
    await vm.handleAddRoleSubmit()
    expect(apiAssignRole).not.toHaveBeenCalled()
    vm.addRoleFormRef = { validate: (cb: any) => cb(false) }
    await vm.handleAddRoleSubmit()
    await flushPromises()
    expect(apiAssignRole).not.toHaveBeenCalled()
    vm.addRoleTarget = null
    vm.addRoleFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddRoleSubmit()
    await flushPromises()
    expect(apiAssignRole).not.toHaveBeenCalled()
  })

  it('handleAddRoleSubmit 成功：expires_at 空 → undefined；有值 → 透传', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addRoleTarget = { user_id: 9 } as any
    vm.addRoleForm.role_id = 'manager'
    vm.addRoleForm.expires_at = ''
    vm.addRoleDialogVisible = true
    vm.addRoleFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddRoleSubmit()
    await flushPromises()
    expect(apiAssignRole).toHaveBeenCalledWith({
      user_id: 9,
      role_id: 'manager',
      expires_at: undefined,
    })
    expect(ElMessage.success).toHaveBeenCalledWith('角色已分配')
    expect(vm.addRoleDialogVisible).toBe(false)
    expect(vm.addRoleSubmitting).toBe(false)
    vm.addRoleForm.expires_at = '2025-12-31T00:00:00'
    vm.addRoleFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddRoleSubmit()
    await flushPromises()
    expect(apiAssignRole).toHaveBeenCalledWith({
      user_id: 9,
      role_id: 'manager',
      expires_at: '2025-12-31T00:00:00',
    })
  })

  it('handleAddRoleSubmit 失败 → 错误提示且提交态复位', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.addRoleTarget = { user_id: 9 } as any
    vm.addRoleForm.role_id = 'manager'
    apiAssignRole.mockRejectedValueOnce(new Error('net'))
    vm.addRoleFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleAddRoleSubmit()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('分配角色失败')
    expect(vm.addRoleSubmitting).toBe(false)
  })

  it('handleRemoveRole：取消确认 → 不发请求；确认成功/失败两分支；roleId 多级兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    // 用户取消
    confirmMock.mockRejectedValueOnce('cancel')
    await vm.handleRemoveRole({ user_id: 1, username: 'u1' }, { role_id: 'admin', name: '管理员' })
    expect(apiRemoveRole).not.toHaveBeenCalled()
    // 确认成功（role.id 兜底 + roleName 用 name）
    await vm.handleRemoveRole({ user_id: 1, username: 'u1' }, { id: 5, name: '主管' })
    expect(apiRemoveRole).toHaveBeenCalledWith(1, '5')
    expect(ElMessage.success).toHaveBeenCalledWith('角色已移除')
    // 空角色对象 → roleId 空串兜底
    await vm.handleRemoveRole({ user_id: 1, username: 'u1' }, {})
    expect(apiRemoveRole).toHaveBeenCalledWith(1, '')
    // 接口失败
    apiRemoveRole.mockRejectedValueOnce(new Error('net'))
    await vm.handleRemoveRole({ user_id: 1, username: 'u1' }, { role_id: 'admin' })
    expect(ElMessage.error).toHaveBeenCalledWith('移除角色失败')
  })

  it('el-tag close 真实交互触发 handleRemoveRole', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.orgUsersWithRoles = JSON.parse(JSON.stringify(roleUsers))
    await nextTick()
    const tags = wrapper.findAllComponents({ name: 'ElTag' })
    for (const t of tags) t.vm.$emit('close')
    await flushPromises()
    expect(confirmMock).toHaveBeenCalled()
    expect(apiRemoveRole).toHaveBeenCalled()
  })
})

describe('权限授予（Tab 3）', () => {
  it('loadOrgUsersWithPermissions：聚合权限成功；单用户权限失败被忽略；非数组权限保持空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    apiGetOrgUsers.mockResolvedValueOnce({
      success: true,
      data: [
        { user_id: 1, username: 'a' },
        { id: 2 },
        { user_id: 3, username: 'c' },
      ],
    })
    apiGetUserPerms.mockImplementation((uid: number) => {
      if (uid === 1) return Promise.resolve({ success: true, data: ['user:read'] })
      if (uid === 2) return Promise.resolve({ success: true, data: 'nope' })
      return Promise.reject(new Error('net'))
    })
    await vm.loadOrgUsersWithPermissions()
    expect(vm.orgUsersWithPerms).toHaveLength(3)
    expect(vm.orgUsersWithPerms[0].permissions).toEqual(['user:read'])
    expect(vm.orgUsersWithPerms[1].permissions).toEqual([])
    expect(vm.permsLoading).toBe(false)
  })

  it('loadOrgUsersWithPermissions：非数组响应 → 置空；异常 → 提示；未选组织 → 返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await vm.loadOrgUsersWithPermissions()
    expect(apiGetOrgUsers).not.toHaveBeenCalled()
    await selectOrg(wrapper)
    apiGetOrgUsers.mockResolvedValueOnce({ success: false, data: [] })
    await vm.loadOrgUsersWithPermissions()
    expect(vm.orgUsersWithPerms).toEqual([])
    apiGetOrgUsers.mockRejectedValueOnce(new Error('net'))
    await vm.loadOrgUsersWithPermissions()
    expect(ElMessage.error).toHaveBeenCalledWith('加载组织用户失败')
    expect(vm.orgUsersWithPerms).toEqual([])
    expect(vm.permsLoading).toBe(false)
  })

  it('权限卡片渲染各分支 + 「授予权限」按钮打开对话框', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.orgUsersWithPerms = JSON.parse(JSON.stringify(permUsers))
    await nextTick()
    expect(wrapper.text()).toContain('user:read')
    expect(wrapper.text()).toContain('暂无权限')
    vm.grantPermForm.permission = 'dirty'
    vm.grantPermForm.expires_at = 'dirty'
    const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes('授予权限'))
    expect(btn).toBeDefined()
    await btn!.trigger('click')
    expect(vm.grantPermTarget.user_id).toBe(1)
    expect(vm.grantPermForm).toEqual({ permission: '', expires_at: '' })
    expect(vm.grantPermDialogVisible).toBe(true)
  })

  it('handleGrantPermSubmit：formRef 空 / 校验失败 / 无目标 → 均不发请求', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.grantPermFormRef = undefined
    await vm.handleGrantPermSubmit()
    expect(apiGrantPerm).not.toHaveBeenCalled()
    vm.grantPermFormRef = { validate: (cb: any) => cb(false) }
    await vm.handleGrantPermSubmit()
    await flushPromises()
    expect(apiGrantPerm).not.toHaveBeenCalled()
    vm.grantPermTarget = null
    vm.grantPermFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleGrantPermSubmit()
    await flushPromises()
    expect(apiGrantPerm).not.toHaveBeenCalled()
  })

  it('handleGrantPermSubmit 成功：expires_at 空 → undefined；有值 → 透传', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.grantPermTarget = { user_id: 9 } as any
    vm.grantPermForm.permission = 'user:read'
    vm.grantPermForm.expires_at = ''
    vm.grantPermDialogVisible = true
    vm.grantPermFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleGrantPermSubmit()
    await flushPromises()
    expect(apiGrantPerm).toHaveBeenCalledWith({
      user_id: 9,
      permission: 'user:read',
      expires_at: undefined,
    })
    expect(ElMessage.success).toHaveBeenCalledWith('权限已授予')
    expect(vm.grantPermDialogVisible).toBe(false)
    expect(vm.grantPermSubmitting).toBe(false)
    vm.grantPermForm.expires_at = '2025-12-31T00:00:00'
    vm.grantPermFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleGrantPermSubmit()
    await flushPromises()
    expect(apiGrantPerm).toHaveBeenCalledWith({
      user_id: 9,
      permission: 'user:read',
      expires_at: '2025-12-31T00:00:00',
    })
  })

  it('handleGrantPermSubmit 失败 → 错误提示且提交态复位', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    vm.grantPermTarget = { user_id: 9 } as any
    vm.grantPermForm.permission = 'user:read'
    apiGrantPerm.mockRejectedValueOnce(new Error('net'))
    vm.grantPermFormRef = { validate: (cb: any) => cb(true) }
    await vm.handleGrantPermSubmit()
    await flushPromises()
    expect(ElMessage.error).toHaveBeenCalledWith('授予权限失败')
    expect(vm.grantPermSubmitting).toBe(false)
  })

  it('handleRevokePermission：取消确认 → 不发请求；确认成功/失败两分支；tag close 交互', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    await selectOrg(wrapper)
    // 用户取消
    confirmMock.mockRejectedValueOnce('cancel')
    await vm.handleRevokePermission({ user_id: 1, username: 'u1' }, 'user:read')
    expect(apiRevokePerm).not.toHaveBeenCalled()
    // 确认成功
    await vm.handleRevokePermission({ user_id: 1, username: 'u1' }, 'user:read')
    expect(apiRevokePerm).toHaveBeenCalledWith(1, 'user:read')
    expect(ElMessage.success).toHaveBeenCalledWith('权限已撤销')
    // 接口失败
    apiRevokePerm.mockRejectedValueOnce(new Error('net'))
    await vm.handleRevokePermission({ user_id: 1, username: 'u1' }, 'user:read')
    expect(ElMessage.error).toHaveBeenCalledWith('撤销权限失败')
    // el-tag close 真实交互
    vm.orgUsersWithPerms = JSON.parse(JSON.stringify(permUsers))
    await nextTick()
    const tags = wrapper.findAllComponents({ name: 'ElTag' })
    for (const t of tags) t.vm.$emit('close')
    await flushPromises()
    expect(apiRevokePerm.mock.calls.length).toBeGreaterThanOrEqual(3)
  })

  it('工具栏「刷新」按钮重新加载组织用户', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await selectOrg(wrapper)
    apiGetOrgUsers.mockClear()
    const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes('刷新'))
    expect(btn).toBeDefined()
    await btn!.trigger('click')
    await flushPromises()
    expect(apiGetOrgUsers).toHaveBeenCalledWith(7, false)
  })
})
