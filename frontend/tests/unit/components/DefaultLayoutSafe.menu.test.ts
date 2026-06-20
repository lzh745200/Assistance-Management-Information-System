import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

describe('DefaultLayoutSafe 侧边栏回归校验', () => {
  const layoutPath = resolve(process.cwd(), 'src/layouts/DefaultLayoutSafe.vue')
  const routerPath = resolve(process.cwd(), 'src/router/index.ts')
  const layoutSource = readFileSync(layoutPath, 'utf8')
  const routerSource = readFileSync(routerPath, 'utf8')

  it('"经费管理"菜单定义正确且不重复', () => {
    // Layout refactored to use el-menu-item index instead of path prop
    expect(layoutSource).toContain('index="/funds"')
    expect(layoutSource).toContain('经费管理')
    expect(layoutSource).toContain('经费申请')
  })

  it('不再存在管理员无条件放行逻辑（避免重复菜单）', () => {
    expect(layoutSource).not.toContain('if (adminRoles.includes(role)) return true')
    // Layout refactored — permission check moved to roleAccess utility
  })

  it('侧边栏配置的菜单路径均存在于路由定义中', () => {
    // Extract menu paths from layout source. Filter out '/' which is a
    // breadcrumb home link (el-breadcrumb-item :to="{ path: '/' }"), not a
    // sidebar menu item — the regex cannot distinguish menu paths from
    // breadcrumb/router-link destinations by pattern alone.
    const menuPaths = [...layoutSource.matchAll(/path:\s*'([^']+)'/g)]
      .map(m => m[1])
      .filter(p => p !== '/')
    const routePaths = [...routerSource.matchAll(/path:\s*\"([^\"]+)\"/g)].map(m => m[1])
    const fullRoutes = new Set<string>(routePaths.filter(p => p.startsWith('/')))
    routePaths
      .filter(p => !p.startsWith('/') && !p.startsWith(':'))
      .forEach(p => fullRoutes.add(`/${p}`))

    const missing = [...new Set(menuPaths)].filter(p => !fullRoutes.has(p))
    expect(missing).toEqual([])
  })
})
