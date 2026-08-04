import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, h } from 'vue'
import { mount } from '@vue/test-utils'
import { useUploadHeaders } from '@/composables/useUploadHeaders'

vi.mock('@/api/request', () => ({
  getCsrfToken: vi.fn(() => Promise.resolve('mock-csrf')),
}))

vi.mock('@/utils/authStorage', () => ({
  AuthStorage: { getToken: vi.fn(() => 'mock-token') },
}))

import { getCsrfToken } from '@/api/request'
import { AuthStorage } from '@/utils/authStorage'

function mountHost() {
  let api: any
  const Comp = defineComponent({
    setup() {
      api = useUploadHeaders()
      return () => h('div')
    },
  })
  const w = mount(Comp, { attachTo: document.body })
  return { w, getApi: () => api }
}

describe('useUploadHeaders（el-upload CSRF 修复）', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('挂载后预取 CSRF 并携带 Authorization + X-CSRF-Token', async () => {
    const { w, getApi } = mountHost()
    await vi.waitFor(() => expect(getCsrfToken).toHaveBeenCalled())
    const api = getApi()
    expect(api.uploadHeaders.value).toMatchObject({
      Authorization: 'Bearer mock-token',
      'X-CSRF-Token': 'mock-csrf',
    })
    w.unmount()
  })

  it('无 token 时仅携带 X-CSRF-Token', async () => {
    ;(AuthStorage.getToken as any).mockReturnValue('')
    const { w, getApi } = mountHost()
    await vi.waitFor(() => expect(getCsrfToken).toHaveBeenCalled())
    const api = getApi()
    expect(api.uploadHeaders.value['X-CSRF-Token']).toBe('mock-csrf')
    expect(api.uploadHeaders.value.Authorization).toBeUndefined()
    w.unmount()
  })

  it('ensureCsrf 可手动重新触发', async () => {
    const { w, getApi } = mountHost()
    const api = getApi()
    ;(getCsrfToken as any).mockClear()
    api.ensureCsrf()
    await vi.waitFor(() => expect(getCsrfToken).toHaveBeenCalled())
    w.unmount()
  })
})
