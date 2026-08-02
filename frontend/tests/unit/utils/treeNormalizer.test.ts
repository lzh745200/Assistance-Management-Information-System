import { describe, it, expect } from 'vitest'
import { normalizeTreeNode, normalizeTreeNodes } from '@/utils/treeNormalizer'

describe('utils/treeNormalizer', () => {
  describe('normalizeTreeNode', () => {
    it('数字 id 前加下划线前缀', () => {
      const out = normalizeTreeNode({ id: 1, name: '总部' })
      expect(out.id).toBe('_1')
    })

    it('id 为 0 时同样加前缀', () => {
      expect(normalizeTreeNode({ id: 0, name: 'x' }).id).toBe('_0')
    })

    it('字符串 id 原样保留', () => {
      expect(normalizeTreeNode({ id: 'org-1', name: 'x' }).id).toBe('org-1')
    })

    it('无 id 时使用 key', () => {
      expect(normalizeTreeNode({ key: 'k1', name: 'x' }).id).toBe('k1')
    })

    it('无 id/key 时基于 name 生成回退键', () => {
      const out = normalizeTreeNode({ name: 'abcdefghijklmnopqrstuvwxyz' })
      expect(out.id).toBe('_node_abcdefghijklmnopqrst')
    })

    it('无 id/key/name 时生成空回退键', () => {
      expect(normalizeTreeNode({}).id).toBe('_node_')
    })

    it('label 缺失时回退到 name', () => {
      const out = normalizeTreeNode({ id: 1, name: '总部' })
      expect(out.label).toBe('总部')
    })

    it('label 存在时优先使用 label', () => {
      const out = normalizeTreeNode({ id: 1, name: 'n', label: 'l' })
      expect(out.label).toBe('l')
    })

    it('带非空 children 时递归规范化', () => {
      const out = normalizeTreeNode({
        id: 1,
        name: 'root',
        children: [{ id: 2, name: 'child' }],
      })
      expect(out.children).toEqual([{ id: '_2', name: 'child', label: 'child', children: undefined, leaf: true }])
      expect(out.leaf).toBe(false)
    })

    it('空 children 时 leaf 为 true', () => {
      const out = normalizeTreeNode({ id: 1, name: 'x', children: [] })
      expect(out.children).toEqual([])
      expect(out.leaf).toBe(true)
    })

    it('无 children 时 children 为 undefined,显式 leaf 生效', () => {
      const out = normalizeTreeNode({ id: 1, name: 'x', leaf: false })
      expect(out.children).toBeUndefined()
      expect(out.leaf).toBe(false)
    })

    it('无 children 且无 leaf 时默认 leaf true', () => {
      const out = normalizeTreeNode({ id: 1, name: 'x' })
      expect(out.leaf).toBe(true)
    })

    it('children 非数组时视为无 children', () => {
      const out = normalizeTreeNode({ id: 1, name: 'x', children: { a: 1 } } as any)
      expect(out.children).toBeUndefined()
      expect(out.leaf).toBe(true)
    })
  })

  describe('normalizeTreeNodes', () => {
    it('映射整个数组', () => {
      const out = normalizeTreeNodes([
        { id: 1, name: 'a' },
        { id: 2, name: 'b', children: [{ id: 3, name: 'c' }] },
      ])
      expect(out).toHaveLength(2)
      expect(out[0].id).toBe('_1')
      expect(out[1].children![0].id).toBe('_3')
    })
  })
})
