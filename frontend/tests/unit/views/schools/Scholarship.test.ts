/**
 * views/schools/Scholarship.vue 覆盖率攻坚（四指标 100%）
 * 覆盖：学校信息/学生列表加载全分支、年度选项计算、本地筛选、字典映射、
 * 新增/编辑对话框、提交/删除/导入全部成功失败路径、模板 v-model 与内联事件处理器。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

// vi.mock 工厂提升求值，引用对象须先放入 vi.hoisted 初始化
const { routeParams, pushSafeMock, ElMessage, logError, api } = vi.hoisted(() => {
  return {
    routeParams: { id: '7' } as Record<string, string>,
    pushSafeMock: vi.fn(),
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
    logError: vi.fn(),
    api: {
      get: vi.fn(),
      listScholarshipStudents: vi.fn(),
      createScholarshipStudent: vi.fn(),
      updateScholarshipStudent: vi.fn(),
      deleteScholarshipStudent: vi.fn(),
      importScholarshipStudents: vi.fn(),
    },
  }
})

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: routeParams }),
}))

vi.mock('@/composables/useRouterSafe', () => ({
  useRouterSafe: () => ({ pushSafe: pushSafeMock }),
  safeRouteParam: (v: any) => v,
}))

vi.mock('element-plus', () => ({
  ElMessage,
}))

vi.mock('@/utils/logger', () => ({
  logger: { error: logError, warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}))

vi.mock('@/api/schools', () => ({ schoolsApi: api }))

import Scholarship from '@/views/schools/Scholarship.vue'

const studentA = {
  id: 1,
  student_name: '小明',
  grade: '三年级',
  year: 2024,
  amount: 500,
  status: 'approved',
  reason: '家庭困难',
  contact_info: '138',
  remarks: 'r',
}
const studentB = { id: 2, student_name: '小红', year: 2023, status: 'pending' }

function mountComp() {
  // el-dialog/el-popconfirm 需渲染具名插槽（footer/reference）；
  // el-table-column 注入三行样本覆盖 amount ?? 0 与状态映射两侧
  return mount(Scholarship, {
    global: {
      renderStubDefaultSlot: true,
      stubs: {
        'el-dialog': {
          name: 'ElDialog',
          template: '<div class="el-dialog-stub"><slot /><slot name="footer" /></div>',
          emits: ['update:modelValue'],
        },
        'el-popconfirm': {
          name: 'ElPopconfirm',
          template: '<div class="el-popconfirm-stub"><slot name="reference" /><slot /></div>',
          emits: ['confirm'],
        },
        'el-table-column': {
          name: 'ElTableColumn',
          template:
            '<div class="el-table-column-stub"><slot :row="rowA" /><slot :row="rowB" /><slot :row="rowC" /></div>',
          data() {
            return {
              rowA: { ...studentA },
              rowB: { id: 3, student_name: '无金额', status: 'weird' }, // amount 缺失 + 未知状态
              rowC: { id: 4, student_name: '空状态', status: '' }, // 状态 falsy → 待审批
            }
          },
        },
      },
    },
  })
}

beforeEach(() => {
  vi.resetAllMocks()
  routeParams.id = '7'
  api.get.mockResolvedValue({ name: '阳光小学' })
  api.listScholarshipStudents.mockResolvedValue({ items: [studentA, studentB] })
  api.createScholarshipStudent.mockResolvedValue({})
  api.updateScholarshipStudent.mockResolvedValue({})
  api.deleteScholarshipStudent.mockResolvedValue({})
  api.importScholarshipStudents.mockResolvedValue({})
})

describe('挂载与数据加载', () => {
  it('onMounted 加载学校名称与学生列表', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(api.get).toHaveBeenCalledWith(7)
    expect(vm.schoolName).toBe('阳光小学')
    expect(api.listScholarshipStudents).toHaveBeenCalledWith('7', undefined)
    expect(vm.students).toHaveLength(2)
    expect(vm.filteredStudents).toHaveLength(2)
    expect(vm.loading).toBe(false)
    await nextTick() // schoolName 标签 v-if 分支渲染
    expect(wrapper.text()).toContain('阳光小学')
  })

  it('loadSchoolName：响应空 → 空串；异常 → 记日志', async () => {
    api.get.mockResolvedValue(null)
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).schoolName).toBe('')
    wrapper.unmount()

    api.get.mockRejectedValue(new Error('net'))
    wrapper = mountComp()
    await flushPromises()
    expect(logError).toHaveBeenCalled()
  })

  it('loadData：schoolId 为空（route 参数缺失 → ?? 兜底）→ 直接返回', async () => {
    delete routeParams.id
    const wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).schoolId).toBe('')
    expect(api.listScholarshipStudents).not.toHaveBeenCalled()
  })

  it('loadData：数组响应、null 响应与异常分支', async () => {
    api.listScholarshipStudents.mockResolvedValue([studentA])
    let wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).students).toHaveLength(1)
    wrapper.unmount()

    // res 为 null → res?.items || res || [] 全兜底
    api.listScholarshipStudents.mockResolvedValue(null)
    wrapper = mountComp()
    await flushPromises()
    expect((wrapper.vm as any).students).toEqual([])
    wrapper.unmount()

    api.listScholarshipStudents.mockRejectedValue(new Error('net'))
    wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(ElMessage.error).toHaveBeenCalledWith('加载资助学生失败')
    expect(vm.loading).toBe(false)
  })

  it('yearOptions：合并学生年度并倒序；filterYear 不在列表时前置', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const years = vm.yearOptions
    const current = new Date().getFullYear()
    expect(years).toContain(current)
    expect(years).toContain(2024)
    expect(years).toContain(2023)
    for (let i = 1; i < years.length; i++) expect(years[i - 1]).toBeGreaterThanOrEqual(years[i])
    vm.filterYear = 1999
    await nextTick()
    expect(vm.yearOptions[0]).toBe(1999)
  })

  it('filterLocal：按状态筛选与清空', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filterStatus = 'approved'
    vm.filterLocal()
    expect(vm.filteredStudents).toEqual([studentA])
    vm.filterStatus = ''
    vm.filterLocal()
    expect(vm.filteredStudents).toHaveLength(2)
  })

  it('statusTagType 全映射与未知兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    expect(vm.statusTagType('pending')).toBe('warning')
    expect(vm.statusTagType('approved')).toBe('primary')
    expect(vm.statusTagType('disbursed')).toBe('success')
    expect(vm.statusTagType('completed')).toBe('info')
    expect(vm.statusTagType('other')).toBe('info')
  })
})

describe('新增/编辑对话框', () => {
  it('openDialog 无参 → 重置表单（year 取 filterYear）', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.filterYear = 2023
    vm.openDialog()
    expect(vm.editingStudent).toBeNull()
    expect(vm.dialogVisible).toBe(true)
    expect(vm.form).toMatchObject({ student_name: '', year: 2023, status: 'pending', amount: 0 })
    vm.dialogVisible = false
    vm.filterYear = undefined
    vm.openDialog()
    expect(vm.form.year).toBe(new Date().getFullYear())
  })

  it('openDialog 带行 → 填充；字段缺失 → 各级兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.openDialog(studentA)
    expect(vm.editingStudent).toEqual(studentA)
    expect(vm.form.student_name).toBe('小明')
    expect(vm.form.amount).toBe(500)
    vm.openDialog({ id: 9 })
    expect(vm.form).toMatchObject({
      student_name: '',
      year: new Date().getFullYear(),
      amount: 0,
      status: 'pending',
    })
  })

  it('handleSubmit：formRef 为空 / 校验失败 → 直接返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = undefined
    await vm.handleSubmit()
    expect(api.createScholarshipStudent).not.toHaveBeenCalled()
    vm.formRef = { validate: vi.fn().mockRejectedValue(new Error('invalid')) }
    await vm.handleSubmit()
    expect(api.createScholarshipStudent).not.toHaveBeenCalled()
  })

  it('handleSubmit 新建与编辑成功路径', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = { validate: vi.fn().mockResolvedValue(true) }
    vm.openDialog()
    vm.form.student_name = '新学生'
    api.listScholarshipStudents.mockClear()
    await vm.handleSubmit()
    expect(api.createScholarshipStudent).toHaveBeenCalledWith(
      '7',
      expect.objectContaining({ student_name: '新学生' })
    )
    expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    expect(vm.dialogVisible).toBe(false)
    expect(api.listScholarshipStudents).toHaveBeenCalled()
    expect(vm.submitting).toBe(false)

    vm.openDialog(studentA)
    // Vue 重渲染会把模板 ref 重新同步为 el-form stub，需在每次提交前重新赋 mock
    vm.formRef = { validate: vi.fn().mockResolvedValue(true) }
    await vm.handleSubmit()
    expect(api.updateScholarshipStudent).toHaveBeenCalledWith(
      '7',
      1,
      expect.objectContaining({ student_name: '小明' })
    )
    expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
  })

  it('handleSubmit 失败：message 与兜底文案', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    vm.formRef = { validate: vi.fn().mockResolvedValue(true) }
    vm.openDialog()
    api.createScholarshipStudent.mockRejectedValueOnce(new Error('重名'))
    await vm.handleSubmit()
    expect(ElMessage.error).toHaveBeenCalledWith('重名')
    api.createScholarshipStudent.mockRejectedValueOnce({})
    vm.formRef = { validate: vi.fn().mockResolvedValue(true) } // 重渲染会重置模板 ref，重新赋值
    await vm.handleSubmit()
    expect(ElMessage.error).toHaveBeenCalledWith('保存失败')
    expect(vm.submitting).toBe(false)
  })
})

describe('删除', () => {
  it('成功 → 提示并刷新；失败 → message 与兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    api.listScholarshipStudents.mockClear()
    await vm.handleDelete(studentA)
    expect(api.deleteScholarshipStudent).toHaveBeenCalledWith('7', 1)
    expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    expect(api.listScholarshipStudents).toHaveBeenCalled()

    api.deleteScholarshipStudent.mockRejectedValueOnce(new Error('有约束'))
    await vm.handleDelete(studentA)
    expect(ElMessage.error).toHaveBeenCalledWith('有约束')
    api.deleteScholarshipStudent.mockRejectedValueOnce({})
    await vm.handleDelete(studentA)
    expect(ElMessage.error).toHaveBeenCalledWith('删除失败')
  })
})

describe('导入', () => {
  it('handleImport 触发文件选择；ref 缺失时安全返回', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const input = wrapper.find('input[type="file"]').element as HTMLInputElement
    const clickSpy = vi.spyOn(input, 'click').mockImplementation(() => {})
    vm.handleImport()
    expect(clickSpy).toHaveBeenCalled()
    vm.fileInputRef = undefined
    vm.handleImport() // 可选链分支，不抛错
    clickSpy.mockRestore()
  })

  it('handleFileChange：无文件 → 返回；成功 → 导入并清空 input', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const input = document.createElement('input')
    Object.defineProperty(input, 'files', { value: [], configurable: true })
    await vm.handleFileChange({ target: input })
    expect(api.importScholarshipStudents).not.toHaveBeenCalled()

    const file = new File(['x'], 's.xlsx')
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    input.value = 's.xlsx'
    api.listScholarshipStudents.mockClear()
    await vm.handleFileChange({ target: input })
    expect(api.importScholarshipStudents).toHaveBeenCalledWith('7', file)
    expect(ElMessage.success).toHaveBeenCalledWith('导入成功')
    expect(api.listScholarshipStudents).toHaveBeenCalled()
    expect(input.value).toBe('')
  })

  it('handleFileChange 失败：detail / message / 兜底', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const input = document.createElement('input')
    const file = new File(['x'], 's.xlsx')
    Object.defineProperty(input, 'files', { value: [file], configurable: true })

    api.importScholarshipStudents.mockRejectedValueOnce({
      response: { data: { detail: '格式错误' } },
    })
    await vm.handleFileChange({ target: input })
    expect(ElMessage.error).toHaveBeenCalledWith('格式错误')

    api.importScholarshipStudents.mockRejectedValueOnce(new Error('网络错误'))
    await vm.handleFileChange({ target: input })
    expect(ElMessage.error).toHaveBeenCalledWith('网络错误')

    api.importScholarshipStudents.mockRejectedValueOnce({})
    await vm.handleFileChange({ target: input })
    expect(ElMessage.error).toHaveBeenCalledWith('导入失败')
  })
})

describe('模板交互（内联处理器与 v-model 函数覆盖）', () => {
  it('点击返回/新增/编辑/取消按钮与 popconfirm 确认', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any
    const findBtn = (text: string) => {
      const btn = wrapper.findAll('el-button-stub').find((b) => b.text().includes(text))
      expect(btn, text).toBeTruthy()
      return btn!
    }

    await findBtn('返回详情').trigger('click')
    expect(pushSafeMock).toHaveBeenCalledWith('/schools/7')

    await findBtn('新增学生').trigger('click')
    expect(vm.dialogVisible).toBe(true)
    expect(vm.editingStudent).toBeNull()

    await findBtn('编辑').trigger('click')
    expect(vm.editingStudent).toBeTruthy()

    const pops = wrapper.findAllComponents({ name: 'ElPopconfirm' })
    expect(pops.length).toBeGreaterThan(0)
    api.listScholarshipStudents.mockClear()
    pops[0].vm.$emit('confirm')
    await flushPromises()
    expect(api.deleteScholarshipStudent).toHaveBeenCalled()

    vm.dialogVisible = true
    const cancel = wrapper.findAll('el-button-stub').find((b) => b.text().trim() === '取消')
    await cancel!.trigger('click')
    expect(vm.dialogVisible).toBe(false)
  })

  it('全部 v-model 组件触发 update 事件', async () => {
    const wrapper = mountComp()
    await flushPromises()
    const vm = wrapper.vm as any

    const selects = wrapper.findAllComponents({ name: 'ElSelect' })
    expect(selects.length).toBeGreaterThan(0)
    for (const c of selects) c.vm.$emit('update:modelValue', 2023)

    const inputs = wrapper.findAllComponents({ name: 'ElInput' })
    for (const c of inputs) c.vm.$emit('update:modelValue', 'x')
    expect(vm.form.student_name).toBe('x')
    expect(vm.form.remarks).toBe('x')

    const numbers = wrapper.findAllComponents({ name: 'ElInputNumber' })
    for (const c of numbers) c.vm.$emit('update:modelValue', 800)
    expect(vm.form.amount).toBe(800)

    const dialogs = wrapper.findAllComponents({ name: 'ElDialog' })
    for (const d of dialogs) d.vm.$emit('update:modelValue', true)
    expect(vm.dialogVisible).toBe(true)
    await nextTick()
  })
})
