import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GuizhouRegionSelector from '@/components/common/GuizhouRegionSelector.vue'
import {
  GUIZHOU_ALL_CITIES,
  getCountiesByCity,
  getTownshipsByCityCounty,
} from '@/data/guizhouRegion'

const stubs = {
  'el-form-item': {
    name: 'ElFormItem',
    props: ['label'],
    template: '<div class="el-form-item"><slot /></div>',
  },
  'el-select': {
    name: 'ElSelect',
    props: ['modelValue', 'disabled', 'clearable', 'filterable', 'placeholder'],
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

const city = GUIZHOU_ALL_CITIES[0]
const county = getCountiesByCity(city)[0]
const township = getTownshipsByCityCounty(city, county)[0]

describe('common/GuizhouRegionSelector.vue', () => {
  it('renders city/county selects with default showTownship=true', () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: {} },
      global: { stubs },
    })
    expect(wrapper.findAll('select.el-select').length).toBe(3)
  })

  it('hides township select when showTownship=false', () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: {}, showTownship: false },
      global: { stubs },
    })
    expect(wrapper.findAll('select.el-select').length).toBe(2)
  })

  it('populates county and township options from selected city/county', () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city, county } },
      global: { stubs },
    })
    const selects = wrapper.findAll('select.el-select')
    const countySelect = selects[1]
    const townshipSelect = selects[2]
    const countyOptions = countySelect.findAll('option')
    expect(countyOptions.length).toBe(getCountiesByCity(city).length)
    expect(townshipSelect.findAll('option').length).toBe(
      getTownshipsByCityCounty(city, county).length
    )
    expect((countySelect.element as HTMLSelectElement).disabled).toBe(false)
  })

  it('emits update:modelValue clearing county/township when city changes', async () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city, county, township } },
      global: { stubs },
    })
    const citySelect = wrapper.findAll('select.el-select')[0]
    await citySelect.setValue(city)
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({
      city,
      county: undefined,
      township: undefined,
    })
  })

  it('emits update:modelValue with city undefined when cleared', async () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city } },
      global: { stubs },
    })
    const citySelect = wrapper.findAll('select.el-select')[0]
    await citySelect.setValue('')
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({
      city: undefined,
      county: undefined,
      township: undefined,
    })
  })

  it('emits update:modelValue clearing township when county changes', async () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city, county, township } },
      global: { stubs },
    })
    const countySelect = wrapper.findAll('select.el-select')[1]
    await countySelect.setValue(county)
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({
      city,
      county,
      township: undefined,
    })
  })

  it('emits update:modelValue clearing county when county cleared', async () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city, county } },
      global: { stubs },
    })
    const countySelect = wrapper.findAll('select.el-select')[1]
    await countySelect.setValue('')
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({
      city,
      county: undefined,
      township: undefined,
    })
  })

  it('emits update:modelValue when township changes', async () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city, county } },
      global: { stubs },
    })
    const townshipSelect = wrapper.findAll('select.el-select')[2]
    await townshipSelect.setValue(township)
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({
      city,
      county,
      township,
    })
  })

  it('emits update:modelValue with township undefined when township cleared', async () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: { city, county, township } },
      global: { stubs },
    })
    const townshipSelect = wrapper.findAll('select.el-select')[2]
    await townshipSelect.setValue('')
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual({
      city,
      county,
      township: undefined,
    })
  })

  it('disables county select when no city selected', () => {
    const wrapper = mount(GuizhouRegionSelector, {
      props: { modelValue: {} },
      global: { stubs },
    })
    const selects = wrapper.findAll('select.el-select')
    expect((selects[1].element as HTMLSelectElement).disabled).toBe(true)
  })

  it('handles missing modelValue entirely', () => {
    const wrapper = mount(GuizhouRegionSelector, { global: { stubs } })
    const selects = wrapper.findAll('select.el-select')
    expect(selects.length).toBe(3)
    expect((selects[1].element as HTMLSelectElement).disabled).toBe(true)
  })
})
