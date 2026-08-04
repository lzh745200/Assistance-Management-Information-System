import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, enableAutoUnmount, flushPromises } from '@vue/test-utils'
import ActivityFeed from '@/components/dashboard/ActivityFeed.vue'
import { ElMessage } from 'element-plus'

enableAutoUnmount(afterEach)

vi.mock('element-plus', async (importOriginal) => {
  const mod = await importOriginal<typeof import('element-plus')>()
  return { ...mod, ElMessage: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }
})

const stubs = {
  'el-icon': { name: 'ElIcon', template: '<i class="el-icon"><slot /></i>' },
  'el-input': {
    name: 'ElInput',
    props: ['modelValue', 'type', 'rows', 'placeholder'],
    emits: ['update:modelValue'],
    template:
      '<textarea class="el-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
  },
  'el-button': {
    name: 'ElButton',
    props: ['type', 'size'],
    emits: ['click'],
    template: '<button class="el-btn" @click="$emit(\'click\')"><slot /></button>',
  },
  'el-empty': {
    name: 'ElEmpty',
    props: ['description', 'imageSize'],
    template: '<div class="el-empty" />',
  },
}

const activities = [
  { id: 1, type: 'project', content: '项目A开工', time: '2024-01-01 10:00' },
  { id: 2, type: 'fund', content: '资金到账', time: '2024-01-02 11:00' },
  { id: 3, type: 'village', content: '帮扶村调研', time: '2024-01-03 12:00' },
  { id: 4, type: 'system', content: '系统更新', time: '2024-01-04 13:00' },
  { id: 5, type: 'other', content: '未知类型', time: '2024-01-05 14:00' },
]

describe('dashboard/ActivityFeed.vue', () => {
  beforeEach(() => {
    vi.mocked(ElMessage.warning).mockClear()
  })

  it('renders nothing when visible=false', () => {
    const wrapper = mount(ActivityFeed, {
      props: { visible: false, activities },
      global: { stubs },
    })
    expect(wrapper.find('.section-card').isVisible()).toBe(false)
  })

  it('shows empty state when no activities', () => {
    const wrapper = mount(ActivityFeed, { props: { activities: [] }, global: { stubs } })
    expect(wrapper.find('.el-empty').exists()).toBe(true)
    expect(wrapper.find('.activity-list').exists()).toBe(false)
  })

  it('renders activity list with icons per type and fallback icon', () => {
    const wrapper = mount(ActivityFeed, { props: { activities }, global: { stubs } })
    expect(wrapper.findAll('.activity-item').length).toBe(5)
    expect(wrapper.find('.icon-project').exists()).toBe(true)
    expect(wrapper.find('.icon-fund').exists()).toBe(true)
    expect(wrapper.find('.icon-village').exists()).toBe(true)
    expect(wrapper.find('.icon-system').exists()).toBe(true)
    expect(wrapper.find('.icon-other').exists()).toBe(true)
  })

  it('toggles form visibility via 添加动态/取消 button', async () => {
    const wrapper = mount(ActivityFeed, {
      props: { activities: [] },
      global: { stubs },
    })
    const toggle = wrapper.find('button.text-btn')
    await toggle.trigger('click')
    expect(wrapper.find('.activity-add-form').exists()).toBe(true)
    expect(wrapper.find('button.text-btn').text()).toContain('取消')
    await wrapper.find('button.text-btn').trigger('click')
    expect(wrapper.find('.activity-add-form').exists()).toBe(false)
  })

  it('warns when publishing empty content', async () => {
    const wrapper = mount(ActivityFeed, {
      props: { activities: [] },
      global: { stubs },
    })
    await wrapper.find('button.text-btn').trigger('click')
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()
    expect(ElMessage.warning).toHaveBeenCalledWith('请输入动态内容')
    expect(wrapper.emitted('add')).toBeFalsy()
  })

  it('adds activity with content and type, resets form and hides it', async () => {
    const wrapper = mount(ActivityFeed, {
      props: { activities: [] },
      global: { stubs },
    })
    await wrapper.find('button.text-btn').trigger('click')
    const select = wrapper.find('select.activity-select')
    await select.setValue('fund')
    const input = wrapper.find('textarea.el-input')
    await input.setValue('  新动态内容  ')
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[0].trigger('click')
    await flushPromises()

    expect(wrapper.emitted('add')).toBeTruthy()
    expect(wrapper.emitted('add')![0][0]).toEqual({ type: 'fund', content: '  新动态内容  ' })
    expect(wrapper.find('.activity-add-form').exists()).toBe(false)
  })

  it('reset button clears the form', async () => {
    const wrapper = mount(ActivityFeed, {
      props: { activities: [] },
      global: { stubs },
    })
    await wrapper.find('button.text-btn').trigger('click')
    const select = wrapper.find('select.activity-select')
    await select.setValue('system')
    const input = wrapper.find('textarea.el-input')
    await input.setValue('内容')
    const buttons = wrapper.findAll('button.el-btn')
    await buttons[1].trigger('click')
    await flushPromises()
    expect((wrapper.find('select.activity-select').element as HTMLSelectElement).value).toBe(
      'project'
    )
    expect((wrapper.find('textarea.el-input').element as HTMLTextAreaElement).value).toBe('')
  })

  it('renders with default props (visible true, no activities)', () => {
    const wrapper = mount(ActivityFeed, { global: { stubs } })
    expect(wrapper.find('.el-empty').exists()).toBe(true)
  })
})
