import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import A11yDialog from '@/components/common/A11yDialog.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import ChangeHistoryDialog from '@/components/common/ChangeHistoryDialog.vue'
import ExportButton from '@/components/common/ExportButton.vue'
import ImportButton from '@/components/common/ImportButton.vue'
import ProjectProgress from '@/components/dashboard/ProjectProgress.vue'
import ReviewDialog from '@/components/report/ReviewDialog.vue'
import PermissionManager from '@/components/rbac/PermissionManager.vue'

const dialogStub = {
  name: 'ElDialog',
  props: ['modelValue', 'title'],
  template: '<div class="dlg"><slot /><slot name="footer" /></div>',
  emits: ['update:modelValue'],
}

describe('template inline handler coverage', () => {
  it('A11yDialog: 触发 close 事件', async () => {
    const w = mount(A11yDialog, {
      props: { visible: true, title: '对话框' },
      slots: { default: '<div>内容</div>' },
      global: { stubs: { 'el-dialog': dialogStub } },
    })
    const dlg = w.findComponent({ name: 'ElDialog' })
    expect(dlg.exists()).toBe(true)
    dlg.vm.$emit('update:modelValue', false)
    await w.vm.$nextTick()
    expect(w.emitted('close')).toBeTruthy()
  })

  it('BaseInput: 触发 update:modelValue', async () => {
    const w = mount(BaseInput, {
      props: { modelValue: 'v', placeholder: 'p' },
      global: {
        stubs: {
          'el-input': {
            name: 'ElInput',
            props: ['modelValue', 'placeholder'],
            template: '<input class="in" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            emits: ['update:modelValue'],
          },
        },
      },
    })
    const input = w.find('input')
    await input.setValue('new')
    expect(w.emitted('update:modelValue')?.[0]?.[0]).toBe('new')
  })

  it('BaseModal: 触发 close', async () => {
    const w = mount(BaseModal, {
      props: { visible: true, title: 't' },
      slots: { default: '<div>m</div>' },
      global: { stubs: { 'el-dialog': dialogStub } },
    })
    const dlg = w.findComponent({ name: 'ElDialog' })
    expect(dlg.exists()).toBe(true)
    dlg.vm.$emit('update:modelValue', false)
    await w.vm.$nextTick()
    expect(w.emitted('close')).toBeTruthy()
  })

  it('ChangeHistoryDialog: 触发 update:visible', async () => {
    const w = mount(ChangeHistoryDialog, {
      props: { visible: true, history: [{ time: '2024-01-01', action: '创建', user: 'admin' }] },
      global: {
        stubs: {
          'el-dialog': dialogStub,
          'el-timeline': { name: 'ElTimeline', template: '<div class="tl"><slot /></div>' },
          'el-timeline-item': { name: 'ElTimelineItem', props: ['timestamp'], template: '<div class="tli">{{ timestamp }}<slot /></div>' },
        },
      },
    })
    const dlg = w.findComponent({ name: 'ElDialog' })
    expect(dlg.exists()).toBe(true)
    dlg.vm.$emit('update:modelValue', false)
    await w.vm.$nextTick()
    expect(w.emitted('update:visible')).toBeTruthy()
  })

  it('ExportButton: 点击触发 export', async () => {
    const w = mount(ExportButton, {
      global: {
        stubs: { 'el-button': { name: 'ElButton', template: '<button class="btn" @click="$emit(\'click\')"><slot /></button>', emits: ['click'] } },
      },
    })
    await w.find('button').trigger('click')
    expect(w.emitted('export')).toBeTruthy()
  })

  it('ImportButton: 点击触发 import', async () => {
    const w = mount(ImportButton, {
      global: {
        stubs: { 'el-button': { name: 'ElButton', template: '<button class="btn" @click="$emit(\'click\')"><slot /></button>', emits: ['click'] } },
      },
    })
    await w.find('button').trigger('click')
    expect(w.emitted('import')).toBeTruthy()
  })

  it('ProjectProgress: 渲染并点击查看全部', async () => {
    const w = mount(ProjectProgress, {
      props: { visible: true, projects: [{ id: 1, name: '项目A', progress: 50 }] },
      global: {
        stubs: {
          'el-progress': { name: 'ElProgress', props: ['percentage', 'status'], template: '<div class="p">{{ percentage }}%</div>' },
          'el-empty': { name: 'ElEmpty', template: '<div class="e" />' },
          'el-icon': { name: 'ElIcon', template: '<span class="ic"><slot /></span>' },
          DataAnalysis: { name: 'DataAnalysis', template: '<span class="da" />' },
        },
      },
    })
    expect(w.exists()).toBe(true)
    const btn = w.find('button.text-btn')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(w.emitted('viewAll')).toBeTruthy()
    expect(w.find('.project-name').text()).toBe('项目A')
    expect(w.find('.p').exists()).toBe(true)
  })

  it('ProjectProgress: 进度100%与空列表分支', async () => {
    const w = mount(ProjectProgress, {
      props: { visible: true, projects: [{ id: 2, name: '项目B', progress: 100 }] },
      global: {
        stubs: {
          'el-progress': { name: 'ElProgress', props: ['percentage', 'status'], template: '<div class="p">{{ percentage }}%</div>' },
          'el-empty': { name: 'ElEmpty', template: '<div class="e" />' },
          'el-icon': { name: 'ElIcon', template: '<span class="ic"><slot /></span>' },
          DataAnalysis: { name: 'DataAnalysis', template: '<span class="da" />' },
        },
      },
    })
    expect(w.find('.p').text()).toBe('100%')
    const empty = mount(ProjectProgress, {
      props: { visible: true, projects: [] },
      global: {
        stubs: {
          'el-progress': { name: 'ElProgress', template: '<div class="p" />' },
          'el-empty': { name: 'ElEmpty', template: '<div class="e" />' },
          'el-icon': { name: 'ElIcon', template: '<span class="ic"><slot /></span>' },
          DataAnalysis: { name: 'DataAnalysis', template: '<span class="da" />' },
        },
      },
    })
    expect(empty.find('.e').exists()).toBe(true)
  })

  it('PermissionManager: 触发 update:modelValue', async () => {
    const w = mount(PermissionManager, {
      props: { modelValue: ['read'], permissions: [{ key: 'read', label: '读' }] },
      global: {
        stubs: {
          'el-checkbox-group': {
            name: 'ElCheckboxGroup',
            props: ['modelValue'],
            template: '<div class="cg" @update:modelValue="$emit(\'update:modelValue\', $event)"><slot /></div>',
            emits: ['update:modelValue'],
          },
          'el-checkbox': {
            name: 'ElCheckbox',
            props: ['label', 'modelValue'],
            template: '<label class="cb"><input type="checkbox" :checked="checked" @change="$emit(\'update:modelValue\', $event.target.checked)" /><slot /></label>',
            emits: ['update:modelValue'],
          },
        },
      },
    })
    const group = w.findComponent({ name: 'ElCheckboxGroup' })
    expect(group.exists()).toBe(true)
    group.vm.$emit('update:modelValue', ['read', 'write'])
    await w.vm.$nextTick()
    expect(w.emitted('update:modelValue')?.[0]?.[0]).toEqual(['read', 'write'])
  })

  it('ReviewDialog: 触发全部事件', async () => {
    const w = mount(ReviewDialog, {
      props: { visible: true },
      global: {
        stubs: {
          'el-dialog': dialogStub,
          'el-button': { name: 'ElButton', template: '<button class="btn" @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
          'el-input': { name: 'ElInput', template: '<input class="i" @input="$emit(\'update:modelValue\', $event.target.value)" />', emits: ['update:modelValue'] },
          'el-form': { name: 'ElForm', template: '<div class="f"><slot /></div>' },
          'el-form-item': { name: 'ElFormItem', template: '<div class="fi"><slot /></div>' },
          'el-rate': { name: 'ElRate', template: '<div class="r" />' },
          'el-select': { name: 'ElSelect', template: '<div class="s" />' },
        },
      },
    })
    const dlg = w.findComponent({ name: 'ElDialog' })
    dlg.vm.$emit('update:modelValue', false)
    const buttons = w.findAll('button')
    expect(buttons.length).toBe(3)
    await buttons[0].trigger('click')
    await buttons[1].trigger('click')
    await buttons[2].trigger('click')
    const input = w.find('input')
    await input.setValue('意见')
    await w.vm.$nextTick()
    expect(w.emitted('close')).toBeTruthy()
    expect(w.emitted('approve')).toBeTruthy()
    expect(w.emitted('reject')).toBeTruthy()
  })
})
