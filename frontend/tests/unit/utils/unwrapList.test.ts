import { describe, it, expect } from 'vitest'
import { unwrapList } from '@/utils/unwrapList'

describe('utils/unwrapList', () => {
  it('format 1: { items, total }', () => {
    const r = unwrapList({ items: [1, 2, 3], total: 3 })
    expect(r).toEqual({ items: [1, 2, 3], total: 3 })
  })

  it('format 1: { items } no total -> total = items.length', () => {
    const r = unwrapList({ items: [1, 2] })
    expect(r).toEqual({ items: [1, 2], total: 2 })
  })

  it('format 2: { code, data: { items, total } }', () => {
    const r = unwrapList({ code: 200, data: { items: ['a', 'b'], total: 10 } })
    expect(r).toEqual({ items: ['a', 'b'], total: 10 })
  })

  it('format 2: data.items no total -> total = items.length', () => {
    const r = unwrapList({ code: 200, data: { items: ['x'] } })
    expect(r).toEqual({ items: ['x'], total: 1 })
  })

  it('null res -> { items: [], total: 0 }', () => {
    expect(unwrapList(null)).toEqual({ items: [], total: 0 })
  })

  it('undefined res -> { items: [], total: 0 }', () => {
    expect(unwrapList(undefined)).toEqual({ items: [], total: 0 })
  })

  it('empty object -> { items: [], total: 0 }', () => {
    expect(unwrapList({})).toEqual({ items: [], total: 0 })
  })

  it('only data without items -> empty', () => {
    expect(unwrapList({ data: {} })).toEqual({ items: [], total: 0 })
  })
})
