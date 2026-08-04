import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, enableAutoUnmount, flushPromises } from '@vue/test-utils'
import ProgressDialog from '@/components/common/ProgressDialog.vue'
import { ElMessage } from 'element-plus'

enableAutoUnmount(afterEach)

const addProgressMock = vi.hoisted(() => vi.fn())
vi.mock('@/stores/project', () => ({
  useProjectStore: () => ({ addProjectProgress: addProgressMock }),
}))
vi.mock('element-plus', async (importOriginal) => {
  const mod = await importOriginal<typeof import('element-plus')>()
  return { ...mod, ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }
})

const stubs = {
  'el-dialog': {
    name: 'ElDialog',
    props: ['modelValue', 'title', 'beforeClose'],
    emits: ['update:modelValue'],
    template:
      '<div v-if="modelValue" class="el-dialog"><slot /></div><div v-if="modelValue" class="el-dialog-footer"><slot name="footer" /></div>',
  },
  'el-form': {
    name: 'ElForm',
    props: ['model', 'rules', 'labelWidth'],
    methods: {
      validate: () => formValidateMock(),
      resetFields: () => {},
    },
    template: '<form class="el-form"><slot /></form>',
  },
  'el-form-item': {
    name: 'ElFormItem',
    props: ['label', 'prop'],
    template: '<div class="el-form-item"><slot /></div>',
  },
  'el-input-number': {
    name: 'ElInputNumber',
    props: ['modelValue', 'min', 'max', 'controlsPosition'],
    emits: ['update:modelValue'],
    template:
      '<input class="el-input-number" :value="modelValue" type="number" @input="$emit(\'update:modelValue\', Number($event.target.value))" />',
  },
  'el-input': {
    name: 'ElInput',
    props: ['modelValue', 'type', 'rows', 'placeholder'],
    emits: ['update:modelValue'],
    template:
      '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  },
  'el-button': {
    name: 'ElButton',
    props: ['type', 'loading'],
    emits: ['click'],
    template: '<button class="el-btn" @click="$emit(\'click\')"><slot /></button>',
  },
}

const formValidateMock = vi.hoisted(() => vi.fn(() => Promise.resolve(true)))

function mountDialog(props: Partial<{ projectId: number; projectName: string; visible: boolean }> = {}) {
  return mount(ProgressDialog, {
    props: { projectId: 1, projectName: '项目A', visible: true, ...props },
    global: { stubs },
  })
}

describe('common/ProgressDialog.vue', () => {
  beforeEach(() => {
    addProgressMock.mockReset().mockResolvedValue({})
    formValidateMock.mockReset().mockResolvedValue(true)
    vi.mocked(ElMessage.success).mockClear()
  })

  it('renders dialog with project name in title', () => {
    const wrapper = mountDialog()
    expect(wrapper.find('.el-dialog').exists()).toBe(true)
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    expect(dialog.props('title')).toContain('项目A')
  })

  it('does not render content when visible=false', () => {
    const wrapper = mountDialog({ visible: false })
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('resets form when visible becomes true', async () => {
    const wrapper = mountDialog({ visible: false })
    const input = () => wrapper.find('.el-input-number').element as HTMLInputElement
    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(input().value).toBe('0')
    await wrapper.setProps({ visible: false })
    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(input().value).toBe('0')
  })

  it('handleClose emits close via 取消 button', async () => {
    const wrapper = mountDialog()
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('dialog update:modelValue forwards update:visible', async () => {
    const wrapper = mountDialog()
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', false)
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('update:visible')).toBeTruthy()
    expect(wrapper.emitted('update:visible')![0][0]).toBe(false)
  })

  it('submits when validation passes, shows success, emits success and close', async () => {
    const wrapper = mountDialog()
    const input = wrapper.find('.el-input-number')
    await input.setValue(60)
    const textareas = wrapper.findAll('.el-input')
    await textareas[0].setValue('进展顺利，完成主体工程')
    await textareas[1].setValue('资金紧张')
    await textareas[2].setValue('申请追加预算')

    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()

    expect(formValidateMock).toHaveBeenCalled()
    expect(addProgressMock).toHaveBeenCalledWith({
      project_id: 1,
      progress_percentage: 60,
      description: '进展顺利，完成主体工程',
      challenges: '资金紧张',
      next_steps: '申请追加预算',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('进度汇报成功')
    expect(wrapper.emitted('success')).toBeTruthy()
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('does not submit when validation fails', async () => {
    formValidateMock.mockResolvedValue(false)
    const wrapper = mountDialog()
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect(addProgressMock).not.toHaveBeenCalled()
  })

  it('handles store rejection in catch/finally', async () => {
    addProgressMock.mockRejectedValue(new Error('server error'))
    const wrapper = mountDialog()
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect(addProgressMock).toHaveBeenCalled()
    expect(wrapper.emitted('success')).toBeFalsy()
  })
})
