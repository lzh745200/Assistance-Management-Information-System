import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/request', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

import { useOrganizationStore } from '@/stores/organization'
import { get, post, put, del } from '@/api/request'

const mockGet = get as ReturnType<typeof vi.fn>
const mockPost = post as ReturnType<typeof vi.fn>
const mockPut = put as ReturnType<typeof vi.fn>
const mockDel = del as ReturnType<typeof vi.fn>

describe('useOrganizationStore', () => {
  let store: ReturnType<typeof useOrganizationStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useOrganizationStore()
    vi.clearAllMocks()
  })

  it('initializes with defaults', () => {
    expect(store.orgs).toEqual([])
    expect(store.current).toBeNull()
    expect(store.tree).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('fetchOrganizations populates orgs', async () => {
    mockGet.mockResolvedValueOnce({
      code: 200,
      data: [{ id: 1, name: 'Org A' }],
    })
    await store.fetchOrganizations()
    expect(store.orgs).toHaveLength(1)
    expect(store.loading).toBe(false)
  })

  it('fetchOrganization loads single org', async () => {
    mockGet.mockResolvedValueOnce({ code: 200, data: { id: 1, name: 'Org A' } })
    await store.fetchOrganization(1)
    expect(store.current).toEqual({ id: 1, name: 'Org A' })
  })

  it('fetchTree populates tree', async () => {
    mockGet.mockResolvedValueOnce({
      code: 200,
      data: [{ id: 1, name: 'Root', children: [] }],
    })
    await store.fetchTree()
    expect(store.tree).toHaveLength(1)
  })

  it('createOrganization adds to list', async () => {
    mockPost.mockResolvedValueOnce({
      code: 200,
      data: { id: 1, name: 'New Org' },
    })
    await store.createOrganization({ name: 'New Org' })
    expect(store.orgs).toHaveLength(1)
  })

  it('updateOrganization modifies item', async () => {
    store.orgs = [{ id: 1, name: 'Old' }]
    mockPut.mockResolvedValueOnce({ code: 200 })
    await store.updateOrganization(1, { name: 'Updated' })
    expect(store.orgs[0].name).toBe('Updated')
  })

  it('deleteOrganization removes item', async () => {
    store.orgs = [{ id: 1 }, { id: 2 }]
    mockDel.mockResolvedValueOnce({ code: 200 })
    await store.deleteOrganization(1)
    expect(store.orgs).toHaveLength(1)
  })

  it('fetchOrganizations handles errors', async () => {
    mockGet.mockRejectedValueOnce(new Error('fail'))
    await store.fetchOrganizations()
    expect(store.orgs).toEqual([])
    expect(store.loading).toBe(false)
  })
})
