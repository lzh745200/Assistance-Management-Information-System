import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import QiannanRegionSelector from '@/components/common/QiannanRegionSelector.vue'
import { QIANNAN_COUNTIES } from '@/data/guizhouRegion'

const stubs = {
  'el-row': { name: 'ElRow', props: ['gutter'], template: '<div class="el-row"><slot /></div>' },
  'el-col': { name: 'ElCol', props: ['span'], template: '<div class="el-col"><slot /></div>' },
  'el-form-item': {
    name: 'ElFormItem',
    props: ['label', 'labelWidth'],
    template: '<div class="el-form-item"><slot /></div>',
  },
  'el-input': {
    name: 'ElInput',
    props: ['modelValue', 'disabled', 'placeholder'],
    template: '<input class="el-input" :value="modelValue" :disabled="disabled" :placeholder="placeholder" />',
  },
  'el-select': {
    name: 'ElSelect',
    props: ['modelValue', 'disabled', 'clearable', 'placeholder'],
    emits: ['update:modelValue'],
    template:
      '<select class="el-select" :value="modelValue" :disabled="disabled" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
  },
  'el-option': {
    name: 'ElOption',
    props: ['label', 'value'],
    template: '<option :value="value" />',
  },
}

describe('common/QiannanRegionSelector.vue', () => {
  it('renders fixed province/city and county options', () => {
    const wrapper = mount(QiannanRegionSelector, { global: { stubs } })
    const inputs = wrapper.findAll('input.el-input')
    expect(inputs[0].attributes('value')).toBe('贵州省')
    expect(inputs[1].attributes('value')).toBe('黔南布依族苗族自治州')
    expect((inputs[0].element as HTMLInputElement).disabled).toBe(true)
    const countySelect = wrapper.find('select.el-select')
    expect(countySelect.findAll('option').length).toBe(QIANNAN_COUNTIES.length)
  })

  it('emits update:modelValue and change on county change', async () => {
    const wrapper = mount(QiannanRegionSelector, { global: { stubs } })
    const countySelect = wrapper.find('select.el-select')
    await countySelect.setValue(QIANNAN_COUNTIES[0])
    expect(wrapper.emitted('update:modelValue')![0][0]).toBe(QIANNAN_COUNTIES[0])
    expect(wrapper.emitted('change')![0][0]).toBe(QIANNAN_COUNTIES[0])
  })

  it('applies disabled, clearable and placeholder props', () => {
    const wrapper = mount(QiannanRegionSelector, {
      props: { modelValue: '都匀市', disabled: true, clearable: false, countyPlaceholder: '选择县' },
      global: { stubs },
    })
    const countySelect = wrapper.find('select.el-select')
    expect((countySelect.element as HTMLSelectElement).disabled).toBe(true)
    expect(countySelect.attributes('value')).toBe('都匀市')
  })

  it('hides labels when showLabels=false', () => {
    const wrapper = mount(QiannanRegionSelector, {
      props: { showLabels: false, labelWidth: '80px' },
      global: { stubs },
    })
    const items = wrapper.findAll('.el-form-item')
    expect(items.length).toBe(3)
  })

  it('uses default label width and placeholders', () => {
    const wrapper = mount(QiannanRegionSelector, { global: { stubs } })
    const inputs = wrapper.findAll('input.el-input')
    expect(inputs[0].attributes('placeholder')).toBe('贵州省')
    expect(inputs[1].attributes('placeholder')).toBe('黔南布依族苗族自治州')
    expect(wrapper.findComponent({ name: 'ElSelect' }).props('placeholder')).toBe('请选择县/市')
  })
})
