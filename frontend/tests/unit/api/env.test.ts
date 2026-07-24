import { describe, it, expect, vi, beforeEach } from 'vitest'

// env.ts 只从 '@/api/request' 导入 get（自动拆信封，resolve body 即可）
const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn().mockResolvedValue({}) }))

vi.mock('@/api/request', () => ({
  get: (...args: any[]) => mockGet(...args),
}))

import { checkEnv, envApi } from '@/api/env'

describe('api/env', () => {
  beforeEach(() => vi.clearAllMocks())

  it('checkEnv GET /env/check 透传返回值', async () => {
    const body = {
      system: { python_version: '3.12', platform: 'win32', env_mode: 'prod' },
      packages: { fastapi: '0.100' },
      missing_packages: [],
    }
    mockGet.mockResolvedValueOnce(body)
    const r = await checkEnv()
    expect(mockGet).toHaveBeenCalledWith('/env/check')
    expect(r).toBe(body)
  })

  it('envApi.check 转发到 checkEnv', async () => {
    const body = { missing_packages: ['x'] }
    mockGet.mockResolvedValueOnce(body)
    const r = await envApi.check()
    expect(mockGet).toHaveBeenCalledWith('/env/check')
    expect(r).toBe(body)
  })
})
