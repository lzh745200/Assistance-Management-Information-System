import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn(),
  apiRequest: vi.fn(),
}))

import { projectsApi, projectApi } from '@/api/projects'
import api from '@/api/request'

const mockGet = api.get as ReturnType<typeof vi.fn>
const mockPost = api.post as ReturnType<typeof vi.fn>
const mockPut = api.put as ReturnType<typeof vi.fn>
const mockDelete = api.delete as ReturnType<typeof vi.fn>

describe('projectsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('list calls GET /projects', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: [] } })
    await projectsApi.list({ page: 1 })
    expect(mockGet).toHaveBeenCalledWith('/projects', { params: { page: 1 } })
  })

  it('get calls GET /projects/:id', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.get(1)
    expect(mockGet).toHaveBeenCalledWith('/projects/1')
  })

  it('create calls POST /projects', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.create({ name: 'New' })
    expect(mockPost).toHaveBeenCalledWith('/projects', { name: 'New' })
  })

  it('update calls PUT /projects/:id', async () => {
    mockPut.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.update(1, { name: 'Updated' })
    expect(mockPut).toHaveBeenCalledWith('/projects/1', { name: 'Updated' })
  })

  it('delete calls DELETE /projects/:id', async () => {
    mockDelete.mockResolvedValueOnce({})
    await projectsApi.delete(1)
    expect(mockDelete).toHaveBeenCalledWith('/projects/1')
  })

  it('getById calls GET /projects/:id', async () => {
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.getById(1)
    expect(mockGet).toHaveBeenCalledWith('/projects/1')
  })

  it('getStats calls GET /projects/stats', async () => {
    mockGet.mockResolvedValueOnce({ data: {} })
    await projectsApi.getStats()
    expect(mockGet).toHaveBeenCalledWith('/projects/stats')
  })

  it('exportList calls with responseType blob', async () => {
    mockGet.mockResolvedValueOnce({ data: {} })
    await projectsApi.exportList({ format: 'xlsx' })
    expect(mockGet).toHaveBeenCalledWith('/projects/export', {
      params: { format: 'xlsx' },
      responseType: 'blob',
    })
  })

  it('importData sends FormData', async () => {
    mockPost.mockResolvedValueOnce({ data: { count: 5 } })
    const file = new File(['data'], 'test.xlsx')
    await projectsApi.importData(file)
    expect(mockPost).toHaveBeenCalled()
    const callArgs = mockPost.mock.calls[0]
    expect(callArgs[0]).toBe('/projects/import')
    expect(callArgs[1]).toBeInstanceOf(FormData)
    expect(callArgs[2]?.headers?.['Content-Type']).toBe('multipart/form-data')
  })

  it('uploadFiles sends FormData with multiple files', async () => {
    mockPost.mockResolvedValueOnce({ data: { files: [] } })
    const files = [new File(['a'], 'a.txt'), new File(['b'], 'b.txt')]
    await projectsApi.uploadFiles(1, files)
    expect(mockPost).toHaveBeenCalled()
    const callArgs = mockPost.mock.calls[0]
    expect(callArgs[0]).toBe('/projects/1/files')
    expect(callArgs[1]).toBeInstanceOf(FormData)
  })

  it('listFiles calls GET /projects/:id/files', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await projectsApi.listFiles(1)
    expect(mockGet).toHaveBeenCalledWith('/projects/1/files')
  })

  it('deleteFile calls DELETE', async () => {
    mockDelete.mockResolvedValueOnce({})
    await projectsApi.deleteFile(1, 2)
    expect(mockDelete).toHaveBeenCalledWith('/projects/1/files/2')
  })

  it('previewFile calls GET', async () => {
    mockGet.mockResolvedValueOnce({ data: { url: 'preview' } })
    await projectsApi.previewFile(1, 2)
    expect(mockGet).toHaveBeenCalledWith('/projects/1/files/2/preview')
  })

  it('getChangeHistory calls GET', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await projectsApi.getChangeHistory(1)
    expect(mockGet).toHaveBeenCalledWith('/projects/1/history/changes')
  })

  it('getFunds calls GET', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await projectsApi.getFunds(1)
    expect(mockGet).toHaveBeenCalledWith('/projects/1/funds')
  })

  it('addFund calls POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.addFund(1, { amount: 1000 })
    expect(mockPost).toHaveBeenCalledWith('/projects/1/funds', { amount: 1000 })
  })

  it('getTasks calls GET', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })
    await projectsApi.getTasks(1)
    expect(mockGet).toHaveBeenCalledWith('/projects/1/tasks')
  })

  it('createTask calls POST', async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.createTask(1, { title: 'Task' })
    expect(mockPost).toHaveBeenCalledWith('/projects/1/tasks', { title: 'Task' })
  })

  it('updateTask calls PUT', async () => {
    mockPut.mockResolvedValueOnce({ data: { id: 1 } })
    await projectsApi.updateTask(1, 2, { status: 'done' })
    expect(mockPut).toHaveBeenCalledWith('/projects/1/tasks/2', { status: 'done' })
  })

  it('deleteTask calls DELETE', async () => {
    mockDelete.mockResolvedValueOnce({})
    await projectsApi.deleteTask(1, 2)
    expect(mockDelete).toHaveBeenCalledWith('/projects/1/tasks/2')
  })

  it('projectApi is an alias of projectsApi', () => {
    expect(projectApi).toBe(projectsApi)
  })
})
