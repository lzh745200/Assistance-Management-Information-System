import { describe, it, expect } from 'vitest'
import { useLoading } from '@/composables/useLoading'

describe('useLoading', () => {
  it('初始 isLoading 为 false', () => {
    const { isLoading } = useLoading()
    expect(isLoading.value).toBe(false)
  })

  it('start() 后 isLoading 为 true', () => {
    const { isLoading, start } = useLoading()
    start()
    expect(isLoading.value).toBe(true)
  })

  it('stop() 后 isLoading 为 false', () => {
    const { isLoading, start, stop } = useLoading()
    start()
    stop()
    expect(isLoading.value).toBe(false)
  })

  it('多次 start/stop 状态正确切换', () => {
    const { isLoading, start, stop } = useLoading()
    start()
    expect(isLoading.value).toBe(true)
    stop()
    expect(isLoading.value).toBe(false)
    start()
    expect(isLoading.value).toBe(true)
  })

  it('isLoading 是响应式 ref', () => {
    const { isLoading, start } = useLoading()
    expect(isLoading.value).toBe(false)
    start()
    expect(isLoading.value).toBe(true)
  })
})
