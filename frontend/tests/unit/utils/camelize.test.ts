import { describe, it, expect } from 'vitest'
import { toCamelCase, toSnakeCase, camelizeDeep, snakeizeDeep } from '@/utils/camelize'

describe('camelize utils', () => {
  it('toCamelCase converts snake to camel', () => {
    expect(toCamelCase('total_amount')).toBe('totalAmount')
    expect(toCamelCase('village_id')).toBe('villageId')
    expect(toCamelCase('alreadyCamel')).toBe('alreadyCamel')
  })

  it('toSnakeCase converts camel to snake', () => {
    expect(toSnakeCase('totalAmount')).toBe('total_amount')
    expect(toSnakeCase('villageId')).toBe('village_id')
    expect(toSnakeCase('already_snake')).toBe('already_snake')
  })

  it('camelizeDeep converts nested keys but keeps envelope meta', () => {
    const input = {
      code: 200,
      success: true,
      data: {
        total_amount: 100,
        village_id: 3,
        items: [{ created_at: '2026-01-01', fund_source: 'military' }],
      },
    }
    const out = camelizeDeep(input)
    expect(out.code).toBe(200)
    expect(out.data.totalAmount).toBe(100)
    expect(out.data.villageId).toBe(3)
    expect(out.data.items[0].createdAt).toBe('2026-01-01')
    expect(out.data.items[0].fundSource).toBe('military')
  })

  it('camelizeDeep handles arrays and null', () => {
    expect(camelizeDeep([{ a_b: 1 }, null])).toEqual([{ aB: 1 }, null])
    expect(camelizeDeep(null)).toBeNull()
    expect(camelizeDeep('str')).toBe('str')
  })

  it('snakeizeDeep converts request body keys', () => {
    const input = { userId: 1, orgId: 2, permissions: [{ permCode: 'x' }] }
    expect(snakeizeDeep(input)).toEqual({
      user_id: 1,
      org_id: 2,
      permissions: [{ perm_code: 'x' }],
    })
  })
})
