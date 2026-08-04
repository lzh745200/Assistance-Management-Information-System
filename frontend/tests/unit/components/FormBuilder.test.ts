import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FormBuilder from '@/components/business/FormBuilder/FormBuilder.vue'

describe('FormBuilder.vue', () => {
  it('修改输入触发 deep watch 并 emit update:model', async () => {
    const w = mount(FormBuilder, {
      props: {
        model: { name: '初始' },
        fields: [{ key: 'name', label: '名称', type: 'text' }],
      },
      global: {
        stubs: {
          'el-form': { name: 'ElForm', template: '<div class="f"><slot /></div>' },
          'el-form-item': { name: 'ElFormItem', template: '<div class="fi"><slot /></div>' },
          'el-input': {
            name: 'ElInput',
            props: ['modelValue'],
            template: '<input class="i" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
            emits: ['update:modelValue'],
          },
          'el-select': { name: 'ElSelect', template: '<div class="s"><slot /></div>' },
          'el-option': { name: 'ElOption', template: '<div class="o" />' },
        },
      },
    })
    const input = w.find('input')
    await input.setValue('新值')
    await new Promise((r) => setTimeout(r, 30))
    expect(w.emitted('update:model')).toBeTruthy()
  })

  it('select 类型字段渲染选项并触发 v-model', async () => {
    const w = mount(FormBuilder, {
      props: {
        model: { city: 'gz' },
        fields: [
          { key: 'city', label: '城市', type: 'select', options: [{ label: '贵阳', value: 'gz' }, { label: '遵义', value: 'zy' }] },
          { key: 'plain', label: '无类型', type: undefined },
        ],
      },
      global: {
        stubs: {
          'el-form': { name: 'ElForm', template: '<div class="f"><slot /></div>' },
          'el-form-item': { name: 'ElFormItem', template: '<div class="fi"><slot /></div>' },
          'el-input': { name: 'ElInput', props: ['modelValue'], template: '<input class="i" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />', emits: ['update:modelValue'] },
          'el-select': { name: 'ElSelect', props: ['modelValue'], template: '<div class="s" @click="$emit(\'update:modelValue\', \'zy\')">{{ modelValue }}<slot /></div>', emits: ['update:modelValue'] },
          'el-option': { name: 'ElOption', template: '<div class="o" />' },
        },
      },
    })
    expect(w.findAll('input').length).toBe(1)
    expect(w.find('.s').exists()).toBe(true)
    expect(w.findAll('.o').length).toBe(2)
    const select = w.findComponent({ name: 'ElSelect' })
    select.vm.$emit('update:modelValue', 'zy')
    await new Promise((r) => setTimeout(r, 30))
    expect(w.emitted('update:model')).toBeTruthy()
  })
})
