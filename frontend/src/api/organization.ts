import { get, post, put, del } from '@/api/request'

export const getOrganizations = (params?: any) => get('/organizations', params)
export const getOrganization = (id: number) => get('/organizations/' + id)
export const getOrganizationTree = () => get('/organizations/tree')
export const createOrganization = (data: any) => post('/organizations', data)
export const updateOrganization = (id: number, data: any) => put('/organizations/' + id, data)
export const deleteOrganization = (id: number) => del('/organizations/' + id)
export const batchUpdateSortOrders = (d: any[]) => post('/organizations/batch-update-sort', d)

export const getMyOrganization = () => get('/organizations/my-organization')

export const getSubordinates = () => get('/organizations/subordinates')

export const getTypeOptions = () => get('/organizations/types/options')

export const getChildren = (orgId: number) => get(`/organizations/${orgId}/children`)

export const getAncestors = (orgId: number) => get(`/organizations/${orgId}/ancestors`)

export const moveOrganization = (orgId: number, data: any) =>
  post(`/organizations/${orgId}/move`, data)

export const activateOrganization = (orgId: number) => post(`/organizations/${orgId}/activate`)

export const deactivateOrganization = (orgId: number) => post(`/organizations/${orgId}/deactivate`)
