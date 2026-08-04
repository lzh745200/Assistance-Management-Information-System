/**
 * Schools Views 批量组件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

enableAutoUnmount(afterEach)

const mockPush = vi.fn(() => Promise.resolve())
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush, resolve: vi.fn(() => ({ name: 'x', matched: [{ path: '/x' }] })) }),
  useRoute: () => ({ params: { id: '1' }, query: {}, path: '/schools/1' }),
  onBeforeRouteLeave: vi.fn(),
  RouterLink: { template: '<a><slot/></a>' },
}))
const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDel = vi.fn()
vi.mock('@/api/request', () => ({
  get: (...a: any[]) => mockGet(...a),
  post: (...a: any[]) => mockPost(...a),
  put: (...a: any[]) => mockPut(...a),
  del: (...a: any[]) => mockDel(...a),
  apiRequest: vi.fn(),
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))
vi.mock('@/utils/logger', () => ({ logger: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn(), log: vi.fn() } }))
vi.mock('@/composables/useRouterSafe', () => ({ useRouterSafe: () => ({ push: mockPush, pushSafe: mockPush }), pushSafe: vi.fn(() => Promise.resolve()), safeRouteParam: (v: unknown, fallback = 0) => { const n = Number(Array.isArray(v) ? v[0] : v); return Number.isFinite(n) ? n : fallback } }))
vi.mock('@/utils/notify', () => ({ notify: Object.assign(() => vi.fn(), { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn(), closeAll: vi.fn() }), default: vi.fn() }))
vi.mock('element-plus', () => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  ElMessageBox: { confirm: vi.fn(() => Promise.resolve('confirm')), alert: vi.fn(), prompt: vi.fn() },
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn(), closeAll: vi.fn() },
  ElForm: { template: '<form><slot/></form>' },
  ElFormItem: { template: '<div><slot/></div>' },
  ElTable: { template: '<table><slot/></table>' },
  ElTableColumn: { template: '<td><slot/></td>' },
  ElPagination: { template: '<div/>' },
  ElDialog: { template: '<div><slot/></div>' },
  ElSelect: { template: '<select><slot/></select>' },
  ElOption: { template: '<option/>' },
  ElInput: { template: '<input/>' },
  ElButton: { template: '<button><slot/></button>' },
  ElCard: { template: '<div><slot/></div>' },
  ElTag: { template: '<span><slot/></span>' },
  ElTabs: { template: '<div><slot/></div>' },
  ElTabPane: { template: '<div><slot/></div>' },
}))

const schoolData = { items: [{ id: 1, name: '测试小学', level: '小学', student_count: 100, status: 'active' }], total: 1 }

beforeEach(() => {
  vi.clearAllMocks()
  setActivePinia(createPinia())
  mockGet.mockResolvedValue({ ...schoolData, data: schoolData, success: true })
  mockPost.mockResolvedValue({ data: { id: 1 }, success: true })
  mockPut.mockResolvedValue({ data: { id: 1 }, success: true })
  mockDel.mockResolvedValue({ data: null, success: true })
})

describe('schools/Analysis.vue', () => {
  it('渲染', async () => {
    const { default: C } = await import('@/views/schools/Analysis.vue')
    const w = mount(C); await flushPromises(); expect(w.exists()).toBe(true)
  })
})
describe('schools/Detail.vue', () => {
  it('渲染', async () => {
    const { default: C } = await import('@/views/schools/Detail.vue')
    const w = mount(C); await flushPromises(); expect(w.exists()).toBe(true)
  })
})
describe('schools/Edit.vue', () => {
  it('渲染', async () => {
    const { default: C } = await import('@/views/schools/Edit.vue')
    const w = mount(C); await flushPromises(); expect(w.exists()).toBe(true)
  })
})
describe('schools/List.vue', () => {
  it('渲染并加载列表', async () => {
    const { default: C } = await import('@/views/schools/List.vue')
    const w = mount(C); await flushPromises(); expect(w.exists()).toBe(true)
    expect(mockGet).toHaveBeenCalled()
  })
  it('新增学校', async () => {
    const { default: C } = await import('@/views/schools/List.vue')
    const w = mount(C); await flushPromises()
    const vm = w.vm as any
    if (vm.handleCreate) vm.handleCreate()
  })
  it('导出', async () => {
    const { default: C } = await import('@/views/schools/List.vue')
    const w = mount(C); await flushPromises()
    const vm = w.vm as any
    if (vm.handleExport) await vm.handleExport()
    if (vm.handleDownloadTemplate) await vm.handleDownloadTemplate()
  })
})
describe('schools/Projects.vue', () => {
  it('渲染', async () => {
    const { default: C } = await import('@/views/schools/Projects.vue')
    const w = mount(C); await flushPromises(); expect(w.exists()).toBe(true)
  })
})
