import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DataTable from '@/components/common/DataTable.vue'

describe('DataTable', () => {
  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'age', label: 'Age', width: 100 },
  ]
  const data = [
    { name: 'Alice', age: 30 },
    { name: 'Bob', age: 25 },
  ]

  it('renders with data and columns', () => {
    const wrapper = mount(DataTable, { props: { data, columns } })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders loading state', () => {
    const wrapper = mount(DataTable, { props: { data: [], columns, loading: true } })
    expect(wrapper.exists()).toBe(true)
  })

  it('renders empty data', () => {
    const wrapper = mount(DataTable, { props: { data: [], columns } })
    expect(wrapper.exists()).toBe(true)
  })
})
