import { get, post, put, del, apiRequest } from '@/api/request'

export const reportApi = {
  // ── 订阅管理 ──
  list: (p?: any) => get('/reports/subscriptions', p),
  getById: (id: number) => get('/reports/subscriptions/' + id),
  create: (d: any) => post('/reports/subscriptions', d),
  update: (id: number, d: any) => put('/reports/subscriptions/' + id, d),
  delete: (id: number) => del('/reports/subscriptions/' + id),
  toggle: (id: number) => post('/reports/subscriptions/' + id + '/toggle'),

  // ── 报表生成与下载 ──
  // 后端 /reports 路由: POST /reports/generate, GET /reports/{id}/download
  generate: (d: any) => post('/reports/generate', d),
  download: (id: number) =>
    apiRequest({ method: 'GET', url: '/reports/' + id + '/download', responseType: 'blob' }),
}
