/**
 * PermissionTreePanel.vue 测试
 * el-table stub 通过 cloneVNode 将 row 注入列 vnode，覆盖：
 * - 权限 → 模块行构建（view/edit 组合）
 * - view/edit 勾选切换 → 权限码增删 + change emit
 * - disabled、状态文案（不可见/只读/完全访问）
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { h, cloneVNode } from 'vue'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import PermissionTreePanel from '@/components/permission/PermissionTreePanel.vue'

enableAutoUnmount(afterEach)

const ElTableStub = {
  props: ['data'],
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
  props: ['label', 'width', 'align', 'row'],
  template: '<td class="stub-td"><slot :row="row" /></td>',
}

const ElCheckboxStub = {
  props: ['modelValue', 'disabled'],
  emits: ['change'],
  methods: {
    onChange(e: Event) {
      this.$emit('change', (e.target as HTMLInputElement).checked)
    },
  },
  template:
    '<input type="checkbox" class="stub-checkbox" :checked="modelValue" :disabled="disabled" @change="onChange" />',
}

function mountPanel(props: Record<string, unknown> = {}) {
  return mount(PermissionTreePanel, {
    props,
    global: {
      stubs: {
        'el-table': ElTableStub,
        'el-table-column': ElTableColumnStub,
        'el-checkbox': ElCheckboxStub,
        'el-alert': { template: '<div class="stub-alert"><slot /></div>' },
      },
    },
  })
}

describe('PermissionTreePanel.vue', () => {
  it('根据权限构建模块行（view/edit 组合）', () => {
    const wrapper = mountPanel({
      permissions: ['user:read', 'user:write', 'village:read'],
    })
    const rows = wrapper.findAll('tr.stub-row')
    expect(rows).toHaveLength(11)

    const boxes = wrapper.findAll('input.stub-checkbox')
    // user: view + edit
    expect(boxes[0].element.checked).toBe(true)
    expect(boxes[1].element.checked).toBe(true)
    // village: view only
    expect(boxes[2].element.checked).toBe(true)
    expect(boxes[3].element.checked).toBe(false)
    // project: none
    expect(boxes[4].element.checked).toBe(false)
    expect(boxes[5].element.checked).toBe(false)

    // 状态文案
    expect(wrapper.text()).toContain('完全访问')
    expect(wrapper.text()).toContain('只读访问')
    expect(wrapper.text()).toContain('模块不可见')
  })

  it('勾选 view 增加 read 权限并 emit change', async () => {
    const wrapper = mountPanel({ permissions: [] })
    const boxes = wrapper.findAll('input.stub-checkbox')
    await boxes[4].setValue(true)

    const emitted = wrapper.emitted('change')!.at(-1)![0] as string[]
    expect(emitted).toContain('project:read')
    expect(emitted).toHaveLength(1)
  })

  it('取消勾选 view 同时移除 read + write 并 emit', async () => {
    const wrapper = mountPanel({ permissions: ['user:read', 'user:write'] })
    const boxes = wrapper.findAll('input.stub-checkbox')
    await boxes[0].setValue(false)

    const emitted = wrapper.emitted('change')!.at(-1)![0] as string[]
    expect(emitted).not.toContain('user:read')
    expect(emitted).not.toContain('user:write')
    expect(emitted).toHaveLength(0)
  })

  it('勾选/取消 edit 权限', async () => {
    const wrapper = mountPanel({ permissions: ['village:read'] })
    const boxes = wrapper.findAll('input.stub-checkbox')
    // village 行 (index 1) edit → boxes[3]
    await boxes[3].setValue(true)
    expect(wrapper.emitted('change')!.at(-1)![0]).toContain('village:write')

    await boxes[3].setValue(false)
    const emitted = wrapper.emitted('change')!.at(-1)![0] as string[]
    expect(emitted).not.toContain('village:write')
    expect(emitted).toContain('village:read')
  })

  it('disabled 时所有复选框禁用', () => {
    const wrapper = mountPanel({ permissions: ['user:read'], disabled: true })
    const boxes = wrapper.findAll('input.stub-checkbox')
    expect(boxes[0].attributes('disabled')).toBeDefined()
    expect(boxes[1].attributes('disabled')).toBeDefined()
  })

  it('编辑权限在无查看权限时禁用', () => {
    const wrapper = mountPanel({ permissions: [] })
    const boxes = wrapper.findAll('input.stub-checkbox')
    expect(boxes[1].attributes('disabled')).toBeDefined()
  })

  it('watch permissions 变化时重建模块列表', async () => {
    const wrapper = mountPanel({ permissions: [] })
    expect(wrapper.text()).toContain('模块不可见')
    await wrapper.setProps({ permissions: ['system:read', 'system:write'] })
    const boxes = wrapper.findAll('input.stub-checkbox')
    expect(boxes[20].element.checked).toBe(true)
    expect(boxes[21].element.checked).toBe(true)
    expect(wrapper.text()).toContain('完全访问')
  })

  it('permissions 为 undefined 时安全构建', () => {
    const wrapper = mountPanel()
    expect(wrapper.findAll('tr.stub-row')).toHaveLength(11)
    expect(wrapper.text()).toContain('模块不可见')
  })
})
