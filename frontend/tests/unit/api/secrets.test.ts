import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet, mockPost } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
}))

// src/api/secrets.ts 实际 import：import { get, post } from '@/api/request'
vi.mock('@/api/request', () => ({
  get: mockGet,
  post: mockPost,
  getCsrfToken: vi.fn(() => Promise.resolve("test-csrf"))}))

import {
  getKeyVersions,
  rotateSecrets,
  createSecret,
  revokeSecret,
  cleanupSecrets,
  getSecretsStatus,
} from '@/api/secrets'

describe('api/secrets', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getKeyVersions 调用 GET /secrets/versions 并透传返回值', async () => {
    const body = { versions: [], count: 0 }
    mockGet.mockResolvedValue(body)
    const result = await getKeyVersions()
    expect(mockGet).toHaveBeenCalledWith('/secrets/versions')
    expect(result).toBe(body)
  })

  it('rotateSecrets 带 versionId 时拼接查询字符串', async () => {
    const body = { message: 'ok', new_version: 'v2' }
    mockPost.mockResolvedValue(body)
    const result = await rotateSecrets('v1')
    expect(mockPost).toHaveBeenCalledWith('/secrets/rotate?version_id=v1')
    expect(result).toBe(body)
  })

  it('rotateSecrets 不带参数时无查询字符串', async () => {
    mockPost.mockResolvedValue({ message: 'ok', new_version: 'v2' })
    await rotateSecrets()
    expect(mockPost).toHaveBeenCalledWith('/secrets/rotate')
  })

  it('createSecret 带 key_type 与 expires_days 查询参数', async () => {
    const body = { message: 'ok', version_id: 'v3' }
    mockPost.mockResolvedValue(body)
    const result = await createSecret({ key_type: 'aes', expires_days: 30 })
    expect(mockPost).toHaveBeenCalledWith('/secrets/create?key_type=aes&expires_days=30')
    expect(result).toBe(body)
  })

  it('createSecret 不带参数时无查询字符串', async () => {
    mockPost.mockResolvedValue({ message: 'ok', version_id: 'v3' })
    await createSecret()
    expect(mockPost).toHaveBeenCalledWith('/secrets/create')
  })

  it('revokeSecret 调用 POST /secrets/revoke/{versionId}', async () => {
    const body = { message: 'ok', version_id: 'v1' }
    mockPost.mockResolvedValue(body)
    const result = await revokeSecret('v1')
    expect(mockPost).toHaveBeenCalledWith('/secrets/revoke/v1')
    expect(result).toBe(body)
  })

  it('cleanupSecrets 默认 keep_days=90', async () => {
    mockPost.mockResolvedValue({ message: 'ok', deleted_count: 1 })
    await cleanupSecrets()
    expect(mockPost).toHaveBeenCalledWith('/secrets/cleanup?keep_days=90')
  })

  it('cleanupSecrets 自定义 keep_days', async () => {
    const body = { message: 'ok', deleted_count: 2 }
    mockPost.mockResolvedValue(body)
    const result = await cleanupSecrets(30)
    expect(mockPost).toHaveBeenCalledWith('/secrets/cleanup?keep_days=30')
    expect(result).toBe(body)
  })

  it('getSecretsStatus 调用 GET /secrets/status 并透传返回值', async () => {
    const body = { total_versions: 2, active_versions: 1, requires_rotation: false }
    mockGet.mockResolvedValue(body)
    const result = await getSecretsStatus()
    expect(mockGet).toHaveBeenCalledWith('/secrets/status')
    expect(result).toBe(body)
  })
})
