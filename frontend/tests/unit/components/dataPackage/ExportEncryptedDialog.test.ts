/**
 * components/dataPackage/ExportEncryptedDialog.vue 覆盖率攻坚
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const { ElMessage, mockPost } = vi.hoisted(() => {
  return {
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    mockPost: vi.fn(),
  }
})

vi.mock('element-plus', () => ({
  ElMessage,
  ElMessageBox: { confirm: vi.fn() },
}))

vi.mock('@/api/request', () => ({
  post: mockPost,
  getCsrfToken: vi.fn(() => Promise.resolve('test-csrf')),
}))

import ExportEncryptedDialog from '@/components/dataPackage/ExportEncryptedDialog.vue'

function mountDialog(props = {}) {
  return mount(ExportEncryptedDialog, {
    props: { modelValue: true, ...props },
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-form': { name: 'ElForm', template: '<form><slot /></form>' },
        'el-checkbox-group': { name: 'ElCheckboxGroup', props: ['modelValue'], emits: ['update:modelValue'], template: '<div class="cg-stub"><slot /></div>' },
        'el-checkbox': { name: 'ElCheckbox', props: ['label', 'modelValue'], emits: ['update:modelValue'], template: '<label class="cb-stub" />' },
        'el-input': { name: 'ElInput', props: ['modelValue'], emits: ['update:modelValue'], template: '<div class="input-stub" />' },
      },
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('dataPackage/ExportEncryptedDialog.vue', () => {
  it('打开时重置表单', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.form.password = '12345678'
    wrapper.vm.form.description = '备注'
    await wrapper.setProps({ modelValue: false })
    await wrapper.setProps({ modelValue: true })
    await flushPromises()
    expect(wrapper.vm.form.password).toBe('')
    expect(wrapper.vm.form.description).toBe('')
    wrapper.unmount()
  })

  it('导出成功', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    wrapper.vm.form.password = '12345678'
    mockPost.mockResolvedValue({ message: '加密导出完成' })
    await wrapper.vm.handleExport()
    expect(mockPost).toHaveBeenCalledWith(
      '/data-packages/export-encrypted',
      expect.objectContaining({ password: '12345678', package_type: 'report' })
    )
    expect(ElMessage.success).toHaveBeenCalledWith('加密导出完成')
    expect(wrapper.emitted('success')).toBeTruthy()
    wrapper.unmount()
  })

  it('校验失败直接返回', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.reject(new Error('bad'))) }
    await wrapper.vm.handleExport()
    expect(mockPost).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('接口异常提示错误', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    mockPost.mockRejectedValue({ response: { data: { detail: '加密导出失败' } } })
    await wrapper.vm.handleExport()
    expect(ElMessage.error).toHaveBeenCalledWith('加密导出失败')
    expect(wrapper.vm.submitting).toBe(false)
    // 无 detail 走默认提示
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    mockPost.mockRejectedValue(new Error('net'))
    await wrapper.vm.handleExport()
    expect(ElMessage.error).toHaveBeenCalledWith('加密导出失败')
    wrapper.unmount()
  })
})


  it('模板事件处理器(dialog/checkbox/input update)与 result 无 message 分支', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.findComponent({ name: 'ElDialog' }).vm.$emit('update:modelValue', false)
    expect(wrapper.emitted('update:modelValue')).toContainEqual([false])
    wrapper.findComponent({ name: 'ElCheckboxGroup' }).vm.$emit('update:modelValue', ['funds'])
    expect(wrapper.vm.form.data_types).toEqual(['funds'])
    for (const input of wrapper.findAllComponents({ name: 'ElInput' })) {
      input.vm.$emit('update:modelValue', 'pw123456')
    }
    expect(wrapper.vm.form.password).toBe('pw123456')
    // 成功无 message → 默认提示
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    wrapper.vm.form.password = '12345678'
    mockPost.mockResolvedValue({})
    await wrapper.vm.handleExport()
    expect(ElMessage.success).toHaveBeenCalledWith('加密导出成功')
    wrapper.unmount()
  })

  it('formRef 缺失时直接返回', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.formRef = null
    await wrapper.vm.handleExport()
    expect(mockPost).not.toHaveBeenCalled()
    wrapper.unmount()
})
