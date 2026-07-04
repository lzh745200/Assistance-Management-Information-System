import api from './request'

export const reportApi = {
  // ── 订阅管理 ──
  list: (p?: any) => api.get('/reports/subscriptions', { params: p }),
  getById: (id: number) => api.get('/reports/subscriptions/' + id),
  create: (d: any) => api.post('/reports/subscriptions', d),
  update: (id: number, d: any) => api.put('/reports/subscriptions/' + id, d),
  delete: (id: number) => api.delete('/reports/subscriptions/' + id),
  toggle: (id: number) => api.post('/reports/subscriptions/' + id + '/toggle'),

  // ── 报表生成与下载 ──
  // 后端 /reports 路由: POST /reports/generate, GET /reports/{id}/download
  generate: (d: any) => api.post('/reports/generate', d),
  download: (id: number) => api.get('/reports/' + id + '/download', { responseType: 'blob' }),
}
