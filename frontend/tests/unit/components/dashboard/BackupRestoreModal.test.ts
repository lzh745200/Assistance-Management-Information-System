import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, enableAutoUnmount, flushPromises } from '@vue/test-utils'
import BackupRestoreModal from '@/components/dashboard/BackupRestoreModal.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

enableAutoUnmount(afterEach)

vi.mock('element-plus', async (importOriginal) => {
  const mod = await importOriginal<typeof import('element-plus')>()
  return {
    ...mod,
    ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() },
    ElMessageBox: { confirm: vi.fn(() => Promise.resolve('confirm')) },
  }
})

const stubs = {
  'el-dialog': {
    name: 'ElDialog',
    props: ['modelValue', 'title', 'destroyOnClose'],
    emits: ['update:modelValue'],
    template:
      '<div v-if="modelValue" class="el-dialog"><slot /></div><div v-if="modelValue" class="el-dialog-footer"><slot name="footer" /></div>',
  },
  'el-alert': {
    name: 'ElAlert',
    props: ['type', 'closable', 'showIcon'],
    template: '<div class="el-alert"><slot name="title" /></div>',
  },
  'el-form': {
    name: 'ElForm',
    props: ['labelWidth'],
    template: '<form class="el-form"><slot /></form>',
  },
  'el-form-item': {
    name: 'ElFormItem',
    props: ['label'],
    template: '<div class="el-form-item"><slot /></div>',
  },
  'el-input': {
    name: 'ElInput',
    props: ['modelValue', 'placeholder'],
    emits: ['update:modelValue'],
    template:
      '<input class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  },
  'el-checkbox-group': {
    name: 'ElCheckboxGroup',
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: '<div class="el-checkbox-group"><slot /></div>',
  },
  'el-checkbox': {
    name: 'ElCheckbox',
    props: ['label'],
    template: '<span class="el-checkbox" />',
  },
  'el-upload': {
    name: 'ElUpload',
    props: ['onChange', 'autoUpload', 'limit', 'accept'],
    template: '<div class="el-upload"><slot /></div>',
  },
  'el-icon': { name: 'ElIcon', template: '<i class="el-icon"><slot /></i>' },
  'el-button': {
    name: 'ElButton',
    props: ['type', 'loading'],
    emits: ['click'],
    template: '<button class="el-btn" @click="$emit(\'click\')"><slot /></button>',
  },
}

function mountModal(props: { modelValue: boolean; mode: 'backup' | 'restore' }) {
  return mount(BackupRestoreModal, { props, global: { stubs } })
}

const fakeFile = new File(['data'], 'backup.sql', { type: 'application/sql' })
const kbFile = new File([new Uint8Array(2048)], 'big.db')
const mbFile = new File([new Uint8Array(5 * 1024 * 1024)], 'huge.db')

describe('dashboard/BackupRestoreModal.vue', () => {
  beforeEach(() => {
    vi.mocked(ElMessage.success).mockClear()
    vi.mocked(ElMessage.warning).mockClear()
    vi.mocked(ElMessageBox.confirm).mockClear()
    vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm')
  })

  it('renders backup section with backup title in backup mode', () => {
    const wrapper = mountModal({ modelValue: true, mode: 'backup' })
    expect(wrapper.find('.el-dialog').exists()).toBe(true)
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    expect(dialog.props('title')).toBe('数据备份')
    expect(wrapper.find('.backup-section').exists()).toBe(true)
    expect(wrapper.find('.restore-section').exists()).toBe(false)
  })

  it('renders restore section with restore title in restore mode', () => {
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    expect(dialog.props('title')).toBe('数据恢复')
    expect(wrapper.find('.restore-section').exists()).toBe(true)
    expect(wrapper.find('.backup-section').exists()).toBe(false)
  })

  it('does not render dialog content when modelValue=false', () => {
    const wrapper = mountModal({ modelValue: false, mode: 'backup' })
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('backup mode: emits backup with name and tables, success message, closes', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'backup' })
    await wrapper.find('.el-input').setValue('季度备份')
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()

    expect(wrapper.emitted('backup')).toBeTruthy()
    expect(wrapper.emitted('backup')![0][0]).toEqual({
      name: '季度备份',
      tables: ['projects', 'funds', 'villages', 'users'],
    })
    expect(ElMessage.success).toHaveBeenCalledWith('备份任务已提交')
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('backup options checkbox group updates backupOptions via v-model', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'backup' })
    const group = wrapper.findComponent({ name: 'ElCheckboxGroup' })
    group.vm.$emit('update:modelValue', ['projects'])
    await wrapper.vm.$nextTick()
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect(wrapper.emitted('backup')![0][0]).toEqual({ name: '', tables: ['projects'] })
  })

  it('cancel button hides dialog in backup mode', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'backup' })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('restore mode: warns when no file selected', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect(ElMessage.warning).toHaveBeenCalledWith('请选择备份文件')
    expect(wrapper.emitted('restore')).toBeFalsy()
  })

  it('restore mode: selects file via on-change prop and displays file info', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    const onChange = upload.props('onChange') as (file: any) => void
    onChange({ raw: fakeFile, name: 'backup.sql', size: fakeFile.size })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.file-info').text()).toContain('backup.sql')
    expect(wrapper.find('.file-info').text()).toContain('4 B')
  })

  it('restore mode: clears selectedFile when raw is missing', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    ;(upload.props('onChange') as (file: any) => void)({ name: 'no-raw.sql', size: 1 })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.file-info').exists()).toBe(false)
  })

  it('dialog v-model emits update:modelValue to hide dialog', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'backup' })
    const dialog = wrapper.findComponent({ name: 'ElDialog' })
    dialog.vm.$emit('update:modelValue', false)
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('restore mode: formats file sizes in KB and MB', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    const onChange = upload.props('onChange') as (file: any) => void
    onChange({ raw: kbFile, name: 'big.db', size: kbFile.size })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.file-info').text()).toContain('2.0 KB')

    onChange({ raw: mbFile, name: 'huge.db', size: mbFile.size })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.file-info').text()).toContain('5.0 MB')
  })

  it('restore mode: confirms and emits restore with file, success message, closes', async () => {
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    ;(upload.props('onChange') as (file: any) => void)({ raw: fakeFile, name: 'backup.sql', size: 100 })
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()

    expect(ElMessageBox.confirm).toHaveBeenCalled()
    expect(wrapper.emitted('restore')).toBeTruthy()
    expect(wrapper.emitted('restore')![0][0]).toBe(fakeFile)
    expect(ElMessage.success).toHaveBeenCalledWith('恢复任务已提交')
    expect(wrapper.find('.el-dialog').exists()).toBe(false)
  })

  it('restore mode: handles user cancelling confirm dialog', async () => {
    vi.mocked(ElMessageBox.confirm).mockRejectedValue(new Error('cancel'))
    const wrapper = mountModal({ modelValue: true, mode: 'restore' })
    const upload = wrapper.findComponent({ name: 'ElUpload' })
    ;(upload.props('onChange') as (file: any) => void)({ raw: fakeFile, name: 'b.sql', size: 1 })
    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()

    expect(wrapper.emitted('restore')).toBeFalsy()
    expect(ElMessage.success).not.toHaveBeenCalled()
  })
})
