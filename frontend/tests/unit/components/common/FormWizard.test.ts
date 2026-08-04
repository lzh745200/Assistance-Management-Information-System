import { describe, it, expect, vi, afterEach } from 'vitest'
import { mount, enableAutoUnmount, flushPromises } from '@vue/test-utils'
import FormWizard from '@/components/common/FormWizard.vue'

enableAutoUnmount(afterEach)

const stubs = {
  'el-steps': {
    name: 'ElSteps',
    props: ['active', 'finishStatus', 'alignCenter'],
    template: '<div class="el-steps"><slot /></div>',
  },
  'el-step': {
    name: 'ElStep',
    props: ['title', 'description', 'status'],
    template: '<div class="el-step" />',
  },
  'el-button': {
    name: 'ElButton',
    props: ['type', 'disabled', 'loading'],
    emits: ['click'],
    template:
      '<button class="el-btn" :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
  },
}

const steps = [
  { title: '基础信息', description: '第一步' },
  { title: '资金信息', description: '第二步', validate: () => true },
  { title: '确认提交', description: '第三步' },
]

describe('common/FormWizard.vue', () => {
  it('renders steps and current step slot; step statuses wait/process', () => {
    const wrapper = mount(FormWizard, {
      props: { steps, title: '向导', finishText: '提交' },
      slots: { 'step-0': '<p class="s0">step 0</p>' },
      global: { stubs },
    })
    expect(wrapper.attributes('aria-label')).toBe('向导')
    expect(wrapper.find('.s0').exists()).toBe(true)
    const stepComps = wrapper.findAllComponents({ name: 'ElStep' })
    expect(stepComps[0].props('status')).toBe('process')
    expect(stepComps[1].props('status')).toBe('wait')
    expect(wrapper.findAll('button.el-btn').length).toBe(2)
  })

  it('advances to next step when validation passes and emits step-change', async () => {
    const wrapper = mount(FormWizard, {
      props: { steps },
      slots: { 'step-0': '<p class="s0">s0</p>', 'step-1': '<p class="s1">s1</p>' },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    expect(wrapper.emitted('step-change')).toBeTruthy()
    expect(wrapper.emitted('step-change')![0][0]).toBe(1)
    const stepComps = wrapper.findAllComponents({ name: 'ElStep' })
    expect(stepComps[0].props('status')).toBe('success')
    expect(stepComps[1].props('status')).toBe('process')
    expect(wrapper.find('.s1').exists()).toBe(true)
    expect(wrapper.findAll('button.el-btn').length).toBe(3)
  })

  it('blocks next when step validation fails and shows error status', async () => {
    const failingSteps = [
      { title: 'A', validate: () => false },
      { title: 'B' },
    ]
    const wrapper = mount(FormWizard, {
      props: { steps: failingSteps },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    expect(wrapper.emitted('step-change')).toBeFalsy()
    const stepComps = wrapper.findAllComponents({ name: 'ElStep' })
    expect(stepComps[0].props('status')).toBe('error')
  })

  it('supports async validation and pending state', async () => {
    let resolveValidate!: (v: boolean) => void
    const asyncSteps = [
      {
        title: 'A',
        validate: () =>
          new Promise<boolean>((resolve) => {
            resolveValidate = resolve
          }),
      },
      { title: 'B' },
    ]
    const wrapper = mount(FormWizard, {
      props: { steps: asyncSteps },
      global: { stubs },
    })
    const buttons = wrapper.findAll('button.el-btn')
    const pendingPromise = buttons[0].trigger('click')
    await pendingPromise
    const loadingButton = wrapper.findAllComponents({ name: 'ElButton' })[0]
    expect(loadingButton.props('loading')).toBe(true)
    resolveValidate(true)
    await flushPromises()
    expect(wrapper.emitted('step-change')).toBeTruthy()
  })

  it('finishes on last step and emits finish with formData', async () => {
    const wrapper = mount(FormWizard, {
      props: { steps, finishText: '提交' },
      slots: { 'step-0': 's0', 'step-1': 's1', 'step-2': '<p class="s2">s2</p>' },
      global: { stubs },
    })
    let buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect(wrapper.find('.s2').exists()).toBe(true)
    buttons = wrapper.findAll('button.el-btn')
    const finishButton = buttons.find((b) => b.text().includes('提交'))
    await finishButton!.trigger('click')
    await flushPromises()
    expect(wrapper.emitted('finish')).toBeTruthy()
    expect(wrapper.emitted('finish')![0][0]).toEqual({})
  })

  it('finish blocked when last step validation fails', async () => {
    const failingLast = [
      { title: 'A' },
      { title: 'B', validate: () => false },
    ]
    const wrapper = mount(FormWizard, {
      props: { steps: failingLast, finishText: '提交' },
      slots: { 'step-0': 's0', 'step-1': 's1' },
      global: { stubs },
    })
    let buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect(wrapper.emitted('finish')).toBeFalsy()
  })

  it('goes back with prev button and emits step-change', async () => {
    const wrapper = mount(FormWizard, {
      props: { steps },
      slots: { 'step-0': 's0', 'step-1': 's1' },
      global: { stubs },
    })
    let buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    expect(wrapper.emitted('step-change')![1][0]).toBe(0)
    expect(wrapper.findAll('button.el-btn').length).toBe(2)
  })

  it('reset restores step 0 and clears formData', async () => {
    const wrapper = mount(FormWizard, {
      props: { steps },
      slots: { 'step-0': 's0', 'step-1': 's1' },
      global: { stubs },
    })
    let buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    buttons = wrapper.findAll('button.el-btn')
    await buttons[2].trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('s0')
    expect(wrapper.text()).not.toContain('s1')
    expect(wrapper.findAll('button.el-btn').length).toBe(2)
  })
})
