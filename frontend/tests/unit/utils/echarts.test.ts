import { describe, it, expect } from 'vitest'
import echarts from '@/utils/echarts'
import { registerMilitaryTheme } from '@/utils/echarts-theme'

describe('utils/echarts', () => {
  it('默认导出注册了按需组件的 echarts 实例', () => {
    expect(echarts).toBeDefined()
    expect(typeof echarts.init).toBe('function')
    expect(typeof echarts.use).toBe('function')
  })

  it('echarts-theme 主题注册幂等', () => {
    expect(() => {
      registerMilitaryTheme()
      registerMilitaryTheme()
    }).not.toThrow()
  })
})
