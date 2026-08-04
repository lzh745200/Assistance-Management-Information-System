/**
 * views/auth/GetMachineCode.vue 覆盖率攻坚
 * 覆盖：获取机器码成功/失败、一键复制、导航
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import { nextTick } from 'vue'

enableAutoUnmount(afterEach)

const { ElMessage, mockPushSafe, mockGet, logError, copyMock } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  mockPushSafe: vi.fn(() => Promise.resolve()),
  mockGet: vi.fn(),
  logError: vi.fn(),
  copyMock: vi.fn(() => Promise.resolve(true)),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(() => Promise.resolve()),
    resolve: vi.fn(() => ({ name: 'x', matched: [{ path: '/x' }] })),
  }),
  useRoute: () => ({ params: {}, query: {} }),
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ push: mockPushSafe, pushSafe: mockPushSafe }),
  pushSafe: mockPushSafe,
}))

vi.mock('@/api/request', () => ({
  get: mockGet,
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

vi.mock('@/utils/logger', () => ({
  logger: { error: logError, warn: vi.fn(), info: vi.fn(), debug: vi.fn(), log: vi.fn() },
}))

vi.mock('@/utils/clipboard', () => ({
  copyToClipboard: copyMock,
}))

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: vi.fn(() => Promise.resolve('confirm')), alert: vi.fn() },
  ElNotification: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

import GetMachineCode from '@/views/auth/GetMachineCode.vue'

const machineData = {
  machine_code: 'MC-ABCD-1234',
  verification_code: '5678',
  machine_info: {
    system: 'Linux',
    release: '5.10',
    node: 'host1',
    processor: 'x86_64',
    machine: 'x86_64',
  },
}

async function mountComp() {
  const w = mount(GetMachineCode, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-button': {
          name: 'ElButton',
          template: '<button @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        'el-alert': {
          name: 'ElAlert',
          template: '<div class="el-alert-stub"><slot /><slot name="title" /></div>',
        },
        'el-descriptions': { name: 'ElDescriptions', template: '<dl><slot /></dl>' },
        'el-descriptions-item': {
          name: 'ElDescriptionsItem',
          template: '<div class="el-desc-item-stub"><slot /></div>',
        },
        'el-icon': { name: 'ElIcon', template: '<span><slot /></span>' },
      },
    },
  })
  await flushPromises()
  await nextTick()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGet.mockResolvedValue({ data: { data: machineData } })
})

describe('GetMachineCode.vue', () => {
  it('渲染页面', async () => {
    const w = await mountComp()
    expect(w.find('.public-machine-code-page').exists()).toBe(true)
    expect(w.text()).toContain('获取机器码')
  })

  it('获取机器码成功 → 展示机器信息', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(mockGet).toHaveBeenCalledWith('/machine-code/get-machine-code')
    expect(vm.machineData?.machine_code).toBe('MC-ABCD-1234')
    expect(ElMessage.success).toHaveBeenCalledWith('机器码获取成功')
    expect(vm.loading).toBe(false)
    expect(w.text()).toContain('5678')
  })

  it('获取机器码：响应无 machine_code → 报错', async () => {
    mockGet.mockResolvedValue({ data: { data: {}, message: '未生成机器码' } })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(ElMessage.error).toHaveBeenCalledWith('未生成机器码')
  })

  it('获取机器码：响应为空 → 默认报错', async () => {
    mockGet.mockResolvedValue({ data: { data: {} } })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(ElMessage.error).toHaveBeenCalledWith('获取机器码失败，请重试')
  })

  it('获取机器码：响应整体为空 → 兜底报错', async () => {
    mockGet.mockResolvedValue(null)
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(ElMessage.error).toHaveBeenCalledWith('获取机器码失败，请重试')
  })

  it('获取机器码：data 为空但 response 存在 → 兜底解析', async () => {
    mockGet.mockResolvedValue({ data: null })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(ElMessage.error).toHaveBeenCalledWith('获取机器码失败，请重试')
  })

  it('获取机器码：请求异常带 detail → 优先展示 detail', async () => {
    mockGet.mockRejectedValue({ response: { data: { detail: '服务异常' } } })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(logError).toHaveBeenCalled()
    expect(ElMessage.error).toHaveBeenCalledWith('服务异常')
  })

  it('获取机器码：请求异常带 message → 展示 message', async () => {
    mockGet.mockRejectedValue({ response: { data: { message: '机器码接口错误' } } })
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(ElMessage.error).toHaveBeenCalledWith('机器码接口错误')
  })

  it('获取机器码：请求异常 → 默认文案', async () => {
    mockGet.mockRejectedValue({})
    const w = await mountComp()
    const vm = w.vm as any
    await vm.getMachineCode()
    expect(ElMessage.error).toHaveBeenCalledWith('获取机器码失败，请检查系统服务是否正常')
  })

  it('一键复制全部信息：有数据 → 调用剪贴板', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.machineData = machineData
    vm.copyAllInfo()
    expect(copyMock).toHaveBeenCalledWith(
      '机器码：MC-ABCD-1234\n校验码：5678',
      '全部信息'
    )
  })

  it('一键复制全部信息：无数据 → 直接返回', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.copyAllInfo()
    expect(copyMock).not.toHaveBeenCalled()
  })

  it('返回登录按钮 → pushSafe', async () => {
    const w = await mountComp()
    const btn = w
      .findAll('button')
      .find((b) => b.text().includes('返回登录'))
    expect(btn).toBeTruthy()
    await btn!.trigger('click')
    expect(mockPushSafe).toHaveBeenCalledWith('/login')
  })

  it('复制按钮（校验码/机器码）→ 调用剪贴板', async () => {
    const w = await mountComp()
    const vm = w.vm as any
    vm.machineData = machineData
    await nextTick()
    const copyBtns = w.findAll('button').filter((b) => b.text().trim() === '复制')
    expect(copyBtns.length).toBeGreaterThanOrEqual(2)
    await copyBtns[0].trigger('click')
    expect(copyMock).toHaveBeenCalledWith('5678', '校验码')
    await copyBtns[1].trigger('click')
    expect(copyMock).toHaveBeenCalledWith('MC-ABCD-1234', '机器码')
  })

  it('忘记密码按钮 → pushSafe', async () => {
    const w = await mountComp()
    const btn = w
      .findAll('button')
      .find((b) => b.text().includes('忘记密码'))
    expect(btn).toBeTruthy()
    await btn!.trigger('click')
    expect(mockPushSafe).toHaveBeenCalledWith('/forgot-password')
  })
})
