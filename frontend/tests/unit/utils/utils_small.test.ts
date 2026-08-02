import { describe, it, expect, vi } from 'vitest'
import { unwrapList, unwrapListTyped } from '@/utils/unwrapList'
import { normalizeTreeNode, normalizeTreeNodes } from '@/utils/treeNormalizer'

describe('unwrapList', () => {
  it('直接分页格式 { items, total }', () => {
    expect(unwrapList({ items: [1, 2], total: 2 })).toEqual({ items: [1, 2], total: 2 })
  })
  it('无 total 时回退 items.length', () => {
    expect(unwrapList({ items: [1, 2] })).toEqual({ items: [1, 2], total: 2 })
  })
  it('标准信封 { code, data: { items, total } }', () => {
    expect(unwrapList({ code: 200, data: { items: ['a'], total: 1 } })).toEqual({
      items: ['a'],
      total: 1,
    })
  })
  it('信封无 total 回退 items.length', () => {
    expect(unwrapList({ code: 200, data: { items: ['a', 'b'] } })).toEqual({
      items: ['a', 'b'],
      total: 2,
    })
  })
  it('空响应返回空列表', () => {
    expect(unwrapList(undefined)).toEqual({ items: [], total: 0 })
    expect(unwrapList(null)).toEqual({ items: [], total: 0 })
    expect(unwrapList({})).toEqual({ items: [], total: 0 })
  })
  it('unwrapListTyped 委托给 unwrapList', () => {
    expect(unwrapListTyped({ data: { items: [1], total: 1 } })).toEqual({ items: [1], total: 1 })
  })
})

describe('treeNormalizer', () => {
  it('数字 id 前加下划线前缀', () => {
    expect(normalizeTreeNode({ id: 0, name: 'root' })).toMatchObject({ id: '_0' })
    expect(normalizeTreeNode({ id: 123, name: 'x' })).toMatchObject({ id: '_123' })
  })
  it('字符串 id 原样保留', () => {
    expect(normalizeTreeNode({ id: 'abc', name: 'x' })).toMatchObject({ id: 'abc' })
  })
  it('无 id 时用 key 回退', () => {
    expect(normalizeTreeNode({ key: 'k1', name: 'x' })).toMatchObject({ id: 'k1' })
  })
  it('无 id/key 时用 name 生成稳定 id', () => {
    expect(normalizeTreeNode({ name: '节点' })).toMatchObject({ id: '_node_节点' })
  })
  it('children 递归规范化', () => {
    const node = {
      id: 1,
      name: 'root',
      children: [{ id: 0, name: 'child' }, { name: 'grand' }],
    }
    const out = normalizeTreeNode(node)
    expect(out.id).toBe('_1')
    expect(out.children).toHaveLength(2)
    expect(out.children[0].id).toBe('_0')
  })
  it('空 children 数组规范化为 []', () => {
    expect(normalizeTreeNode({ id: 1, name: 'x', children: [] })).toMatchObject({ children: [] })
  })
  it('normalizeTreeNodes 批量处理', () => {
    const out = normalizeTreeNodes([{ id: 0, name: 'a' }])
    expect(out[0].id).toBe('_0')
  })
})
