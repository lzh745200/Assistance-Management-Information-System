import { describe, it, expect, vi, beforeEach } from 'vitest'
import { runStandaloneTests } from '@/utils/standaloneTest'

describe('utils/standaloneTest', () => {
  beforeEach(() => { vi.restoreAllMocks() })

  it('API ok + localStorage ok -> all passed', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true })
    ;(globalThis as any).fetch = mockFetch
    const results = await runStandaloneTests()
    expect(results).toHaveLength(2)
    expect(results[0]).toMatchObject({ name: 'API连接', passed: true })
    expect(results[1]).toMatchObject({ name: '本地存储', passed: true })
  })

  it('API fails -> API passed=false', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('network error'))
    ;(globalThis as any).fetch = mockFetch
    const results = await runStandaloneTests()
    expect(results[0].passed).toBe(false)
    expect(results[0].error).toBe('network error')
  })

  it('localStorage fails -> local storage passed=false', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: true })
    ;(globalThis as any).fetch = mockFetch
    const origSet = localStorage.setItem
    ;(localStorage as any).setItem = () => { throw new Error('quota') }
    const results = await runStandaloneTests()
    expect(results[1].passed).toBe(false)
    expect(results[1].error).toBe('quota')
    ;(localStorage as any).setItem = origSet
  })
})
