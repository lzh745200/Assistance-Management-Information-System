import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockPost = vi.fn()

vi.mock('@/utils/request', () => ({
  default: { post: (...args: any[]) => mockPost(...args) },
}))

vi.mock('@/api/request', () => ({
  default: { post: (...args: any[]) => mockPost(...args) },
}))

import {
  exportEncryptedPackage,
  uploadEncryptedPackage,
  decryptAndPreview,
  confirmImport,
  downloadPackage,
} from '@/api/dataPackageEncrypted'

describe('api/dataPackageEncrypted', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('exportEncryptedPackage POST /data-packages/export-encrypted', async () => {
    mockPost.mockResolvedValueOnce({ package_id: 1, file_name: 'pkg.zip' })
    await exportEncryptedPackage({ data_types: ['village'] })
    expect(mockPost).toHaveBeenCalledWith('/data-packages/export-encrypted', {
      data_types: ['village'],
    })
  })

  it('uploadEncryptedPackage POST FormData with file (no password)', async () => {
    mockPost.mockResolvedValueOnce({ id: 1, package_code: 'X' })
    const file = new File(['data'], 'pkg.zip')
    await uploadEncryptedPackage(file)
    const [url, formData, config] = mockPost.mock.calls[0]
    expect(url).toBe('/data-packages/upload-encrypted')
    expect(formData).toBeInstanceOf(FormData)
    expect(formData.get('file')).toBe(file)
    expect(formData.get('password')).toBeNull()
    expect(config.headers['Content-Type']).toBe('multipart/form-data')
  })

  it('uploadEncryptedPackage POST FormData with password', async () => {
    mockPost.mockResolvedValueOnce({ id: 1 })
    const file = new File(['data'], 'pkg.zip')
    await uploadEncryptedPackage(file, 'secret')
    const formData = mockPost.mock.calls[0][1]
    expect(formData.get('password')).toBe('secret')
  })

  it('decryptAndPreview POST with password in params', async () => {
    mockPost.mockResolvedValueOnce({ package_id: 1, is_encrypted: true })
    await decryptAndPreview(5, 'secret')
    expect(mockPost).toHaveBeenCalledWith(
      '/data-packages/decrypt-preview/5',
      null,
      { params: { password: 'secret' } },
    )
  })

  it('confirmImport POST conflict_strategy', async () => {
    mockPost.mockResolvedValueOnce({ success: true })
    await confirmImport({ package_id: 5, conflict_strategy: 'OVERWRITE' })
    expect(mockPost).toHaveBeenCalledWith(
      '/data-packages/confirm-import/5',
      { conflict_strategy: 'OVERWRITE' },
    )
  })

  it('confirmImport 支持 SKIP/OVERWRITE/KEEP_BOTH/MERGE 策略', async () => {
    for (const strategy of ['SKIP', 'OVERWRITE', 'KEEP_BOTH', 'MERGE'] as const) {
      mockPost.mockResolvedValueOnce({ success: true })
      await confirmImport({ package_id: 1, conflict_strategy: strategy })
      expect(mockPost).toHaveBeenLastCalledWith(
        `/data-packages/confirm-import/1`,
        { conflict_strategy: strategy },
      )
    }
  })

  it('downloadPackage 返回 URL 字符串', () => {
    expect(downloadPackage(7)).toBe('/api/v1/data-packages/7/download')
  })
})
