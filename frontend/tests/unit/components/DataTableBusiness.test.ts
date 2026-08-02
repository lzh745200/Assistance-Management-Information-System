/**
 * business/DataTable/DataTable.vue 测试
 * 覆盖：数据/列渲染、loading、分页显示/隐藏、page-change 事件
 */
import { describe, it, expect, afterEach } from 'vitest'
import { mount, enableAutoUnmount } from '@vue/test-utils'
import DataTable from '@/components/business/DataTable/DataTable.vue'

enableAutoUnmount(afterEach)

const ElTableStub = {
  props: ['data', 'loading'],
  template:
    '<table class="stub-table"><tbody><tr v-for="(row, i) in data" :key="i"><slot :row="row" /></tr></tbody></table>',
}

const ElTableColumnStub = {
  props: ['label', 'prop', 'width'],
  template: '<td class="stub-col" />',
}

const ElPaginationStub = {
  props: ['total', 'pageSize', 'currentPage'],
  emits: ['update:currentPage', 'current-change'],
  data: () => ({ next: 2 }),
  template:
    '<button class="stub-next" @click="$emit(\'update:currentPage\', $data.next); $emit(\'current-change\', $data.next)">next</button>',
}

function mountTable(props: Record<string, unknown> = {}) {
  return mount(DataTable, {
    props,
    global: {
      stubs: {
        'el-table': ElTableStub,
        'el-table-column': ElTableColumnStub,
        'el-pagination': ElPaginationStub,
      },
    },
  })
}

describe('business/DataTable/DataTable.vue', () => {
  const columns = [
    { key: 'name', label: '名称', width: 120 },
    { key: 'age', label: '年龄' },
  ]

  it('渲染数据行与列', () => {
    const wrapper = mountTable({ data: [{ name: 'A', age: 1 }, { name: 'B', age: 2 }], columns })
    expect(wrapper.findAll('tr')).toHaveLength(2)
    // 每行 2 列
    expect(wrapper.findAll('td.stub-col')).toHaveLength(4)
    expect(wrapper.findAll('td.stub-col')[0].props('prop')).toBe('name')
    expect(wrapper.findAll('td.stub-col')[1].props('prop')).toBe('age')
  })

  it('空数据时无行', () => {
    const wrapper = mountTable({ data: [], columns })
    expect(wrapper.findAll('tr')).toHaveLength(0)
  })

  it('loading prop 透传到表格', () => {
    const wrapper = mountTable({ data: [], columns, loading: true })
    expect(wrapper.find('table.stub-table').props('loading')).toBe(true)
  })

  it('pagination=false 时不渲染分页', () => {
    const wrapper = mountTable({ data: [], columns })
    expect(wrapper.find('button.stub-next').exists()).toBe(false)
  })

  it('pagination=true 时渲染分页并派发 page-change', async () => {
    const wrapper = mountTable({ data: [], columns, pagination: true, total: 100, pageSize: 10 })
    const next = wrapper.find('button.stub-next')
    expect(next.exists()).toBe(true)
    await next.trigger('click')
    expect(wrapper.emitted('page-change')).toEqual([[2]])
  })
})
