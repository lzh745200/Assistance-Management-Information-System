import { describe, it, expect } from 'vitest'
import { useBatchOperation } from '@/composables/useBatchOperation'

describe('useBatchOperation', () => {
  it('初始状态无选中', () => {
    const { selectedItems, selectedCount, isAllSelected, getSelectedList } =
      useBatchOperation<number>()
    expect(selectedItems.value.size).toBe(0)
    expect(selectedCount.value).toBe(0)
    expect(isAllSelected.value).toBe(false)
    expect(getSelectedList()).toEqual([])
  })

  it('toggleSelect 添加项', () => {
    const { toggleSelect, selectedItems, selectedCount, isAllSelected } =
      useBatchOperation<number>()
    toggleSelect(1)
    expect(selectedItems.value.has(1)).toBe(true)
    expect(selectedCount.value).toBe(1)
    expect(isAllSelected.value).toBe(false)
  })

  it('toggleSelect 移除已选项', () => {
    const { toggleSelect, selectedItems, selectedCount } =
      useBatchOperation<number>()
    toggleSelect(1)
    toggleSelect(1)
    expect(selectedItems.value.has(1)).toBe(false)
    expect(selectedCount.value).toBe(0)
  })

  it('selectAll 选中所有项', () => {
    const { selectAll, selectedItems, selectedCount, isAllSelected, getSelectedList } =
      useBatchOperation<number>()
    selectAll([1, 2, 3])
    expect(selectedCount.value).toBe(3)
    expect(isAllSelected.value).toBe(true)
    expect(getSelectedList().sort()).toEqual([1, 2, 3])
  })

  it('clearSelection 清空选择', () => {
    const { selectAll, clearSelection, selectedItems, isAllSelected, selectedCount } =
      useBatchOperation<number>()
    selectAll([1, 2, 3])
    clearSelection()
    expect(selectedItems.value.size).toBe(0)
    expect(isAllSelected.value).toBe(false)
    expect(selectedCount.value).toBe(0)
  })

  it('selectedCount 反映 Set 的大小', () => {
    const { toggleSelect, selectedCount } = useBatchOperation<string>()
    toggleSelect('a')
    toggleSelect('b')
    toggleSelect('c')
    expect(selectedCount.value).toBe(3)
  })

  it('isAllSelected 在 toggleSelect 后为 false', () => {
    const { selectAll, toggleSelect, isAllSelected } = useBatchOperation<number>()
    selectAll([1, 2, 3])
    expect(isAllSelected.value).toBe(true)
    toggleSelect(1)
    expect(isAllSelected.value).toBe(false)
  })

  it('支持对象类型的项', () => {
    interface Item {
      id: number
    }
    const { toggleSelect, getSelectedList } = useBatchOperation<Item>()
    const a: Item = { id: 1 }
    const b: Item = { id: 2 }
    toggleSelect(a)
    toggleSelect(b)
    expect(getSelectedList()).toHaveLength(2)
    expect(getSelectedList()[0].id).toBe(1)
  })
})
