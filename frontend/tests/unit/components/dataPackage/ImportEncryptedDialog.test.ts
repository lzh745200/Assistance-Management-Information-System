/**
 * components/dataPackage/ImportEncryptedDialog.vue 覆盖率攻坚
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

import ImportEncryptedDialog from '@/components/dataPackage/ImportEncryptedDialog.vue'

function mountDialog(props = {}) {
  return mount(ImportEncryptedDialog, {
    props: { modelValue: true, ...props },
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-form': { name: 'ElForm', template: '<form><slot /></form>' },
        'el-upload': {
          name: 'ElUpload',
          props: ['modelValue', 'fileList'],
          emits: ['change', 'remove'],
          template: '<div class="upload-stub"><slot /><slot name="tip" /></div>',
        },
        'el-input': { name: 'ElInput', props: ['modelValue'], emits: ['update:modelValue'], template: '<div class="input-stub" />' },
      },
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('dataPackage/ImportEncryptedDialog.vue', () => {
  it('打开时重置', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.form.password = '12345678'
    wrapper.vm.selectedFile = new File(['x'], 'a.rrs')
    await wrapper.setProps({ modelValue: false })
    await wrapper.setProps({ modelValue: true })
    await flushPromises()
    expect(wrapper.vm.form.password).toBe('')
    expect(wrapper.vm.selectedFile).toBeNull()
    wrapper.unmount()
  })

  it('未选文件时警告', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    await wrapper.vm.handleImport()
    expect(ElMessage.warning).toHaveBeenCalledWith('请先选择数据包文件')
    expect(mockPost).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('导入成功', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.handleFileChange({ raw: new File(['x'], 'a.rrs') })
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    wrapper.vm.form.password = '12345678'
    mockPost.mockResolvedValue({ message: '加密导入完成' })
    await wrapper.vm.handleImport()
    expect(mockPost).toHaveBeenCalledWith('/data-packages/upload-encrypted', expect.any(FormData), expect.any(Object))
    expect(ElMessage.success).toHaveBeenCalledWith('加密导入完成')
    expect(wrapper.emitted('success')).toBeTruthy()
    wrapper.unmount()
  })

  it('校验失败直接返回', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.handleFileChange({ raw: new File(['x'], 'a.rrs') })
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.reject(new Error('bad'))) }
    await wrapper.vm.handleImport()
    expect(mockPost).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('移除文件清空选择', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.handleFileChange({ raw: new File(['x'], 'a.rrs') })
    expect(wrapper.vm.selectedFile).toBeInstanceOf(File)
    wrapper.vm.handleFileRemove()
    expect(wrapper.vm.selectedFile).toBeNull()
    expect(wrapper.vm.fileList).toEqual([])
    wrapper.unmount()
  })

  it('接口异常提示错误', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.vm.handleFileChange({ raw: new File(['x'], 'a.rrs') })
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    mockPost.mockRejectedValue({ response: { data: { detail: '解密失败' } } })
    await wrapper.vm.handleImport()
    expect(ElMessage.error).toHaveBeenCalledWith('解密失败')
    expect(wrapper.vm.submitting).toBe(false)
    wrapper.unmount()
  })
})


  it('模板事件处理器(dialog/upload/input)与分支补齐', async () => {
    const wrapper = mountDialog()
    await flushPromises()
    wrapper.findComponent({ name: 'ElDialog' }).vm.$emit('update:modelValue', false)
    expect(wrapper.emitted('update:modelValue')).toContainEqual([false])
    for (const input of wrapper.findAllComponents({ name: 'ElInput' })) {
      input.vm.$emit('update:modelValue', 'pw123456')
    }
    expect(wrapper.vm.form.password).toBe('pw123456')
    // file.raw 为空 → null
    wrapper.vm.handleFileChange({ raw: null })
    expect(wrapper.vm.selectedFile).toBeNull()
    // formRef 缺失直接返回
    wrapper.vm.handleFileChange({ raw: new File(['x'], 'a.rrs') })
    wrapper.vm.formRef = null
    await wrapper.vm.handleImport()
    expect(mockPost).not.toHaveBeenCalled()
    // success 无 message 默认提示 + err 无 detail 默认提示
    wrapper.vm.formRef = { validate: vi.fn(() => Promise.resolve()) }
    wrapper.vm.form.password = '12345678'
    mockPost.mockResolvedValue({})
    await wrapper.vm.handleImport()
    expect(ElMessage.success).toHaveBeenCalledWith('加密数据包导入成功')
    wrapper.vm.handleFileChange({ raw: new File(['y'], 'b.rrs') })
    mockPost.mockRejectedValue({})
    await wrapper.vm.handleImport()
    expect(ElMessage.error).toHaveBeenCalledWith('导入失败')
    wrapper.unmount()
})
