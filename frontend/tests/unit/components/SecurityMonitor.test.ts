/**
 * SecurityMonitor.vue 测试
 * 覆盖：事件列表渲染（含等级标签全分支）、详情弹窗、卸载清理
 */
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest'
import { h, cloneVNode } from 'vue'
import { mount, flushPromises, enableAutoUnmount } from '@vue/test-utils'
import SecurityMonitor from '@/components/ui/SecurityMonitor.vue'
import { SecurityLevel } from '@/utils/security'

enableAutoUnmount(afterEach)

const mocks = vi.hoisted(() => ({
  messageBox: { alert: vi.fn(), confirm: vi.fn(), prompt: vi.fn() },
}))

vi.mock('element-plus', () => ({
  ElMessageBox: mocks.messageBox,
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
}))

const ElTableStub = {
  props: ['data', 'height'],
  setup(props: any, ctx: any) {
    return () =>
      h(
        'table',
        (props.data || []).map((row: any, i: number) =>
          h(
            'tr',
            { key: i, class: 'stub-row' },
            (ctx.slots.default?.() || []).map((n: any) => cloneVNode(n, { row }))
          )
        )
      )
  },
}

const ElTableColumnStub = {
  props: ['label', 'prop', 'width', 'row'],
  template: '<td class="stub-td"><slot :row="row" /></td>',
}

const ElTagStub = {
  props: ['type'],
  template: '<span class="stub-tag"><slot /></span>',
}

const ElButtonStub = {
  emits: ['click'],
  template: '<button class="stub-btn" @click="$emit(\'click\')"><slot /></button>',
}

const ElCardStub = {
  template: '<div class="stub-card"><div><slot name="header" /></div><slot /></div>',
}

function mountMonitor() {
  return mount(SecurityMonitor, {
    global: {
      stubs: {
        'el-table': ElTableStub,
        'el-table-column': ElTableColumnStub,
        'el-tag': ElTagStub,
        'el-button': ElButtonStub,
        'el-card': ElCardStub,
      },
    },
  })
}

describe('SecurityMonitor.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('挂载后渲染 3 条安全事件及等级标签', async () => {
    const wrapper = mountMonitor()
    await flushPromises()

    expect(wrapper.findAll('tr.stub-row')).toHaveLength(3)
    const tags = wrapper.findAll('span.stub-tag')
    expect(tags).toHaveLength(4) // 3 个等级标签 + 1 个状态标签
    // INTERNAL → info（默认分支）
    expect(tags[1].props('type')).toBe('info')
    // CONFIDENTIAL → primary
    expect(tags[2].props('type')).toBe('primary')
    // SECRET → warning
    expect(tags[3].props('type')).toBe('warning')
    expect(wrapper.text()).toContain('安全监控面板')
    expect(wrapper.text()).toContain('登录成功')
    expect(wrapper.text()).toContain('数据访问')
    expect(wrapper.text()).toContain('权限变更')
  })

  it('getLevelType 覆盖 TOP_SECRET → danger（通过 setupState）', () => {
    const wrapper = mountMonitor()
    const state = (wrapper.vm as any).$.setupState
    expect(state.getLevelType(SecurityLevel.TOP_SECRET)).toBe('danger')
    expect(state.getLevelType(SecurityLevel.SECRET)).toBe('warning')
    expect(state.getLevelType(SecurityLevel.CONFIDENTIAL)).toBe('primary')
    expect(state.getLevelType(SecurityLevel.PUBLIC)).toBe('info')
  })

  it('点击详情 → ElMessageBox.alert 展示事件消息', async () => {
    const wrapper = mountMonitor()
    await flushPromises()
    await wrapper.findAll('button.stub-btn')[0].trigger('click')
    expect(mocks.messageBox.alert).toHaveBeenCalledWith(expect.any(String), '安全事件详情')

    // details 字段存在时优先展示 details
    const state = (wrapper.vm as any).$.setupState
    state.handleDetail({ message: 'm', details: 'd' })
    expect(mocks.messageBox.alert).toHaveBeenCalledWith('d', '安全事件详情')
  })

  it('卸载时清理定时器', async () => {
    const wrapper = mountMonitor()
    await flushPromises()
    wrapper.unmount()
  })
})
