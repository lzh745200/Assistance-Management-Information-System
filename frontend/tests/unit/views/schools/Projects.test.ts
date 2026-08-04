/**
 * views/schools/Projects.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：onMounted 加载、筛选（阶段/日期）、openDialog 新增/编辑、handleSave 全分支、
 * handleDelete、phaseTagType 全分支、模板 v-model 与按钮。
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

const { ElMessage, schoolApiMock, pushSafeMock, routeBox, logError } = vi.hoisted(() => ({
  ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn(), info: vi.fn() },
  schoolApiMock: {
    listProjects: vi.fn(),
    createProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
  },
  pushSafeMock: vi.fn(),
  routeBox: { params: { id: '3' } as Record<string, any> },
  logError: vi.fn(),
}))

vi.mock('vue-router', () => ({ useRoute: () => routeBox }))

vi.mock('element-plus', () => ({ ElMessage }))

vi.mock('@/api/schools', () => ({ schoolApi: schoolApiMock }))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
  safeRouteParam: (v: any) => Number(v) || v,
}))

vi.mock('@/utils/logger', () => ({
  logger: { error: logError, warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}))

import Projects from '@/views/schools/Projects.vue'

const projectImpl = {
  id: 1,
  name: '教学楼',
  category: '教学设施',
  phase: 'implementation',
  budget: 100,
  actual_cost: 60,
  start_date: '2024-01-01T00:00:00',
  end_date: null,
}

const projectCompleted = {
  id: 2,
  name: '操场',
  phase: 'completed',
  budget: 50,
  actual_cost: 50,
  start_date: '2023-06-01T00:00:00',
}

const projectResearch = {
  id: 3,
  name: '调研项目',
  phase: 'research',
  start_date: null,
}

const projectUnknown = { id: 4, name: '未知阶段', phase: 'unknown', start_date: '2024-01-01T00:00:00' }

function mountComp() {
  return mount(Projects, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-table': {
          template:
            '<div class="el-table-stub"><slot name="empty" /><slot name="default" /></div>',
        },
        'el-table-column': {
          name: 'ElTableColumn',
          template:
            '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /><slot :row="rowC" /><slot :row="rowD" /></div>',
          data() {
            return {
              rowA: { ...projectImpl },
              rowB: { ...projectCompleted },
              rowC: { ...projectResearch },
              rowD: { ...projectUnknown },
            }
          },
        },
        'el-select': {
          template:
            '<div class="el-select-stub" @click="$emit(\'update:modelValue\', \'acceptance\'); $emit(\'change\')"><slot /></div>',
        },
        'el-option': { template: '<div class="el-option-stub" />' },
        'el-date-picker': {
          template:
            '<div class="el-date-picker-stub" @click="$emit(\'update:modelValue\', [new Date(2024, 0, 1), new Date(2024, 5, 30)])" />',
        },
        'el-input': {
          template:
            '<div class="el-input-stub" @click="$emit(\'update:modelValue\', \'V\')" />',
        },
        'el-input-number': {
          template:
            '<div class="el-input-number-stub" @click="$emit(\'update:modelValue\', 66)" />',
        },
        'el-button': {
          template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>',
          emits: ['click'],
        },
        'el-tag': { template: '<span class="el-tag-stub"><slot /></span>' },
        'el-dialog': {
          template:
            '<div class="el-dialog-stub" @click="$emit(\'update:modelValue\', false)"><slot /><slot name="footer" /></div>',
        },
        'el-form': { template: '<div class="el-form-stub"><slot /></div>' },
        'el-form-item': { template: '<div class="el-form-item-stub"><slot /></div>' },
        'el-row': { template: '<div class="el-row-stub"><slot /></div>' },
        'el-col': { template: '<div class="el-col-stub"><slot /></div>' },
        'el-popconfirm': {
          template:
            '<div class="el-popconfirm-stub" @click="$emit(\'confirm\', rowA)"><slot name="reference" /></div>',
        },
      },
    },
  })
}

beforeEach(() => {
  vi.resetAllMocks()
  routeBox.params = { id: '3' }
  schoolApiMock.listProjects.mockResolvedValue({
    items: [projectImpl, projectCompleted, projectResearch],
  })
  schoolApiMock.createProject.mockResolvedValue({})
  schoolApiMock.updateProject.mockResolvedValue({})
  schoolApiMock.deleteProject.mockResolvedValue({})
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('挂载与列表', () => {
  it('onMounted 加载项目', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(schoolApiMock.listProjects).toHaveBeenCalledWith(3)
    expect(vm.projects).toHaveLength(3)
    expect(vm.loading).toBe(false)
  })

  it('加载失败 → logger', async () => {
    schoolApiMock.listProjects.mockRejectedValue(new Error('net'))
    const wrapper = mountComp()
    await flushPromises()
    expect(logError).toHaveBeenCalled()
    expect((wrapper.vm as any).loading).toBe(false)
  })

  it('listProjects 无 items → 空数组', async () => {
    schoolApiMock.listProjects.mockResolvedValue({})
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).projects).toEqual([])
  })

  it('返回详情按钮 → pushSafe', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const btn = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('返回详情'))
    await btn!.trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/schools/3')
  })
})

describe('筛选', () => {
  it('按阶段筛选 + 日期范围筛选', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filterPhase = 'implementation'
    await nextTick()
    expect(vm.filteredProjects).toHaveLength(1)
    expect(vm.filteredProjects[0].name).toBe('教学楼')

    vm.filterPhase = ''
    vm.filterDateRange = [new Date(2023, 0, 1), new Date(2023, 11, 31)]
    await nextTick()
    expect(vm.filteredProjects.map((p: any) => p.name)).toEqual(['操场'])

    vm.filterDateRange = [new Date(2024, 0, 1), new Date(2024, 5, 30)]
    await nextTick()
    expect(vm.filteredProjects.map((p: any) => p.name)).toEqual(['教学楼'])

    vm.filterDateRange = null
    await nextTick()
    expect(vm.filteredProjects).toHaveLength(3)
  })

  it('阶段下拉 change → filterProjects', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.find('.el-select-stub').trigger('click')
    expect((wrapper.vm as any).filterPhase).toBe('acceptance')
  })

  it('日期选择器 change', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.find('.el-date-picker-stub').trigger('click')
    expect((wrapper.vm as any).filterDateRange).toHaveLength(2)
  })
})

describe('新增/编辑', () => {
  it('openDialog 新增', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.openDialog()
    expect(vm.editingProject).toBeNull()
    expect(vm.form.name).toBe('')
    expect(vm.form.phase).toBe('research')
    expect(vm.dialogVisible).toBe(true)
  })

  it('openDialog 编辑回填', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.openDialog(projectImpl)
    expect(vm.editingProject).toEqual(projectImpl)
    expect(vm.form.name).toBe('教学楼')
    expect(vm.form.start_date).toBe('2024-01-01T00:00:00')

    vm.openDialog(projectResearch)
    expect(vm.form.start_date).toBeNull()
  })

  it('handleSave：空名称 → warning', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await (wrapper.vm as any).handleSave()
    expect(ElMessage.warning).toHaveBeenCalledWith('请输入项目名称')
  })

  it('handleSave：编辑成功', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.openDialog(projectImpl)
    schoolApiMock.listProjects.mockClear()
    await vm.handleSave()
    expect(schoolApiMock.updateProject).toHaveBeenCalledWith(3, 1, vm.form)
    expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
    expect(vm.dialogVisible).toBe(false)
    expect(schoolApiMock.listProjects).toHaveBeenCalled()
  })

  it('handleSave：新增成功', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.form.name = '新项目'
    schoolApiMock.listProjects.mockClear()
    await vm.handleSave()
    expect(schoolApiMock.createProject).toHaveBeenCalledWith(3, vm.form)
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
  })

  it('handleSave：失败', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.form.name = '新项目'
    schoolApiMock.createProject.mockRejectedValueOnce(new Error('net'))
    await vm.handleSave()
    expect(ElMessage.error).toHaveBeenCalledWith('保存失败')
    expect(vm.saving).toBe(false)
  })

  it('新增项目/编辑按钮', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const add = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('新增项目'))
    await add!.trigger('click')
    expect(vm.dialogVisible).toBe(true)

    vm.dialogVisible = false
    const edit = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('编辑'))
    await edit!.trigger('click')
    expect(vm.dialogVisible).toBe(true)
  })

  it('表单 v-model 更新 + 保存/取消', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    for (const el of wrapper.findAll('.el-input-stub')) {
      await el.trigger('click')
    }
    for (const el of wrapper.findAll('.el-input-number-stub')) {
      await el.trigger('click')
    }
    for (const sel of wrapper.findAll('.el-select-stub')) {
      await sel.trigger('click')
    }
    for (const dp of wrapper.findAll('.el-date-picker-stub')) {
      await dp.trigger('click')
    }
    await flushPromises()
    expect(vm.form.name).toBe('V')
    expect(vm.form.category).toBe('V')
    expect(vm.form.description).toBe('V')
    expect(vm.form.budget).toBe(66)
    expect(vm.form.actual_cost).toBe(66)
    expect(vm.form.phase).toBe('acceptance')
    expect(vm.form.start_date).toHaveLength(2)
    expect(vm.form.end_date).toHaveLength(2)

    schoolApiMock.listProjects.mockClear()
    const save = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('保存'))
    await save!.trigger('click')
    await flushPromises()
    expect(schoolApiMock.createProject).toHaveBeenCalled()

    vm.dialogVisible = true
    const cancel = wrapper.findAll('.el-button-stub').find((b) => b.text().includes('取消'))
    await cancel!.trigger('click')
    expect(vm.dialogVisible).toBe(false)
  })
})

describe('删除', () => {
  it('删除成功/失败', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    schoolApiMock.listProjects.mockClear()
    await vm.handleDelete(projectImpl)
    expect(schoolApiMock.deleteProject).toHaveBeenCalledWith(3, 1)
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    expect(schoolApiMock.listProjects).toHaveBeenCalled()

    schoolApiMock.deleteProject.mockRejectedValueOnce(new Error('net'))
    await vm.handleDelete(projectImpl)
    expect(logError).toHaveBeenCalled()
  })

  it('删除 popconfirm confirm', async () => {
    const wrapper = mountComp()
    await flushPromises()
    schoolApiMock.deleteProject.mockClear()
    await wrapper.find('.el-popconfirm-stub').trigger('click')
    await flushPromises()
    expect(schoolApiMock.deleteProject).toHaveBeenCalled()
  })
})

describe('模板渲染', () => {
  it('phaseTagType 全分支与阶段标签', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.phaseTagType('completed')).toBe('success')
    expect(vm.phaseTagType('implementation')).toBe('primary')
    expect(vm.phaseTagType('acceptance')).toBe('warning')
    expect(vm.phaseTagType('research')).toBe('info')
    expect(vm.phaseTagType('unknown')).toBe('info')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('实施')
    expect(wrapper.text()).toContain('已完成')
    expect(wrapper.text()).toContain('unknown')
  })

  it('日期显示 split 与占位', async () => {
    const wrapper = mountComp()
    await flushPromises()
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('2024-01-01')
    expect(wrapper.text()).toContain('-')
  })
})
