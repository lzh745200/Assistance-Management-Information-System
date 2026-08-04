import { describe, it, expect } from 'vitest'
import DataTable, { DataTable as Named, type Column, type DataTableProps, type DataTableEmits } from '@/components/business/DataTable/index'
import LazyImage, { LazyImage as LazyNamed } from '@/components/common/LazyImage/index'
import Skeleton, { Skeleton as SkeletonNamed } from '@/components/common/Skeleton/index'
import { Permission } from '@/types/rbac'

describe('components re-export index files', () => {
  it('DataTable default + named export are the same component', () => {
    expect(DataTable).toBe(Named)
    expect(typeof DataTable).toBe('object')
  })

  it('LazyImage default + named export are the same component', () => {
    expect(LazyImage).toBe(LazyNamed)
    expect(typeof LazyImage).toBe('object')
  })

  it('Skeleton default + named export are the same component', () => {
    expect(Skeleton).toBe(SkeletonNamed)
    expect(typeof Skeleton).toBe('object')
  })

  it('type-only exports are available at type level', () => {
    const col: Column = { key: 'id', label: 'ID' }
    const props: DataTableProps = { data: [], columns: [col] }
    const emits: DataTableEmits = ['selection-change']
    expect(props.columns[0].label).toBe('ID')
    expect(emits).toContain('selection-change')
    expect(Permission.USER_READ).toBe('user:read')
  })
})
