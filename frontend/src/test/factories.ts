/**
 * 测试数据工厂 — 为常见测试场景生成数据
 * 所有工厂返回普通对象，不依赖外部类型
 */

let _idCounter = 1
export function resetIdCounter() {
  _idCounter = 1
}
export function nextId() {
  return _idCounter++
}

export function buildUser(overrides: Record<string, any> = {}) {
  const id = nextId()
  return {
    id: String(id),
    username: `user_${id}`,
    realName: `用户${id}`,
    role: 'admin',
    email: `user${id}@test.com`,
    phone: `1380000${String(id).padStart(4, '0')}`,
    permissions: ['read', 'write'],
    avatar: '',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function buildVillage(overrides: Record<string, any> = {}) {
  const id = nextId()
  return {
    id: String(id),
    name: `测试村${id}`,
    code: `V${String(id).padStart(4, '0')}`,
    region: '贵州省某县',
    population: 1200,
    area: 15.5,
    status: 'active',
    description: '',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function buildFund(overrides: Record<string, any> = {}) {
  const id = nextId()
  return {
    id: String(id),
    name: `项目资金${id}`,
    amount: 100000,
    usedAmount: 50000,
    remainingAmount: 50000,
    status: 'active',
    source: '中央财政',
    villageId: '1',
    villageName: '测试村',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function buildProject(overrides: Record<string, any> = {}) {
  const id = nextId()
  return {
    id: String(id),
    name: `帮扶项目${id}`,
    code: `P${String(id).padStart(4, '0')}`,
    description: `项目${id}描述`,
    status: 'in_progress',
    budget: 500000,
    usedAmount: 200000,
    villageId: '1',
    villageName: '测试村',
    startDate: '2025-01-01',
    endDate: '2025-12-31',
    responsiblePerson: `负责人${id}`,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function buildPolicy(overrides: Record<string, any> = {}) {
  const id = nextId()
  return {
    id: String(id),
    title: `政策${id}`,
    content: `政策${id}内容详情...`,
    summary: `政策${id}摘要`,
    level: 'national',
    category: 'agriculture',
    publishDate: '2025-01-15',
    department: '农业农村部',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function buildWorkLog(overrides: Record<string, any> = {}) {
  const id = nextId()
  return {
    id: String(id),
    category: 'village',
    content: `操作日志${id}内容`,
    logDate: '2025-01-15',
    userId: '1',
    userName: '操作员',
    createdAt: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function buildListResponse(
  items: any[],
  total?: number,
  overrides: Record<string, any> = {}
) {
  return {
    code: 200,
    message: '成功',
    data: {
      items,
      total: total ?? items.length,
      page: 1,
      page_size: 20,
      ...overrides,
    },
  }
}

export function buildSingleResponse(data: any) {
  return { code: 200, message: '成功', data }
}

export function buildApiError(status = 500, message = '服务器错误') {
  return { status, message }
}
