/**
 * TemplateDownload.vue 测试
 * 覆盖：默认/过滤/自定义模板展示、下载成功、下载失败（detail/message/默认）、loading 状态
 */
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import TemplateDownload from '@/components/templates/TemplateDownload.vue'

enableAutoUnmount(afterEach)

vi.mock('@element-plus/icons-vue', () => ({
  Download: { template: '<i />' },
  Document: { template: '<i />' },
}))

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  downloadBlob: vi.fn(),
  parseContentDisposition: vi.fn((_headers: any, fallback: string) => fallback),
  message: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

vi.mock('@/api/request', () => ({
  default: { get: (...a: any[]) => mocks.get(...a) },
  downloadBlob: (...a: any[]) => mocks.downloadBlob(...a),
  parseContentDisposition: (...a: any[]) => mocks.parseContentDisposition(...a),
}))

vi.mock('element-plus', () => ({ ElMessage: mocks.message }))

const ElButtonStub = {
  props: {
    disabled: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    type: String,
    size: String,
  },
  emits: ['click'],
  template: '<button class="stub-btn" :disabled="disabled" :loading="loading" @click="$emit(\'click\')"><slot /></button>',
}

const ElCardStub = {
  template: '<div class="stub-card"><slot /></div>',
}

function mountTpl(props: Record<string, unknown> = {}) {
  return mount(TemplateDownload, {
    props,
    global: {
      stubs: {
        'el-button': ElButtonStub,
        'el-card': ElCardStub,
        'el-icon': { template: '<i class="stub-icon"><slot /></i>' },
        'el-row': { template: '<div class="stub-row"><slot /></div>' },
        'el-col': { template: '<div class="stub-col"><slot /></div>' },
      },
    },
  })
}

describe('TemplateDownload.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.get.mockResolvedValue({ data: new Blob(['x']), headers: { 'content-disposition': 'a' } })
  })

  it('无 props 时显示全部 4 个模板', () => {
    const wrapper = mountTpl()
    const texts = wrapper.text()
    expect(texts).toContain('帮扶村模板')
    expect(texts).toContain('项目模板')
    expect(texts).toContain('资金模板')
    expect(texts).toContain('学校模板')
    expect(wrapper.findAll('button.stub-btn')).toHaveLength(4)
  })

  it('types 过滤模板', () => {
    const wrapper = mountTpl({ types: ['project', 'fund'] })
    const texts = wrapper.text()
    expect(texts).toContain('项目模板')
    expect(texts).toContain('资金模板')
    expect(texts).not.toContain('学校模板')
    expect(wrapper.findAll('button.stub-btn')).toHaveLength(2)
  })

  it('自定义 templates 优先展示', () => {
    const wrapper = mountTpl({
      templates: [{ type: 'custom', label: '自定义', desc: '自定义描述' }],
    })
    expect(wrapper.text()).toContain('自定义模板')
    expect(wrapper.findAll('button.stub-btn')).toHaveLength(1)
  })

  it('下载成功：调用 get/downloadBlob，展示 loading 后复位', async () => {
    let resolveGet!: (v: any) => void
    mocks.get.mockImplementationOnce(() => new Promise((r) => { resolveGet = r }))
    const wrapper = mountTpl()
    const btn0 = wrapper.findAll('button.stub-btn')[0]
    await btn0.trigger('click')

    // 下载中 → loading 状态
    expect(wrapper.findAll('button.stub-btn')[0].attributes('loading')).toBe('true')
    resolveGet({ data: new Blob(['x']), headers: {} })
    await flushPromises()

    expect(mocks.get).toHaveBeenCalledWith('/import/template', {
      params: { entity_type: 'supported_village' },
      responseType: 'blob',
    })
    expect(mocks.parseContentDisposition).toHaveBeenCalled()
    expect(mocks.downloadBlob).toHaveBeenCalledWith(expect.any(Blob), '帮扶村_导入模板.xlsx')
    expect(wrapper.findAll('button.stub-btn')[0].attributes('loading')).toBe('false')
  })

  it('下载未知类型：文件名回退为 type', async () => {
    const wrapper = mountTpl({
      templates: [{ type: 'mystery', label: '神秘', desc: 'x' }],
    })
    await wrapper.findAll('button.stub-btn')[0].trigger('click')
    await flushPromises()
    expect(mocks.downloadBlob).toHaveBeenCalledWith(expect.any(Blob), 'mystery_导入模板.xlsx')
  })

  it('下载失败：detail / message / 默认错误文案', async () => {
    mocks.get.mockRejectedValueOnce({ response: { data: { detail: '下载失败A' } } })
    const wrapper = mountTpl()
    await wrapper.findAll('button.stub-btn')[0].trigger('click')
    await flushPromises()
    expect(mocks.message.error).toHaveBeenCalledWith('下载失败A')

    mocks.get.mockRejectedValueOnce(new Error('网络错误'))
    await wrapper.findAll('button.stub-btn')[1].trigger('click')
    await flushPromises()
    expect(mocks.message.error).toHaveBeenCalledWith('网络错误')

    mocks.get.mockRejectedValueOnce({})
    await wrapper.findAll('button.stub-btn')[2].trigger('click')
    await flushPromises()
    expect(mocks.message.error).toHaveBeenCalledWith('模板下载失败，请重试')
  })
})
