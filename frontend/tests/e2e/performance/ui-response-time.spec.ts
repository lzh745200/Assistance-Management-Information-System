/**
 * UI 响应时间性能 E2E 测试
 *
 * 测试场景：
 * - 页面加载时间在合理范围内
 * - 列表页面渲染性能
 * - 路由切换响应速度
 */

import { test, expect } from '@playwright/test'
import { login, navigateTo } from '../helpers'

/** 页面加载超时阈值（毫秒） */
const PAGE_LOAD_THRESHOLD = 10000

test.describe('UI 响应时间', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('工作台页面在合理时间内加载', async ({ page }) => {
    const start = Date.now()
    await navigateTo(page, '/dashboard')
    await expect(page.locator('.dashboard-page, .welcome-banner, .stat-card').first()).toBeVisible({
      timeout: PAGE_LOAD_THRESHOLD,
    })
    const duration = Date.now() - start
    console.log(`工作台加载耗时: ${duration}ms`)
    expect(duration).toBeLessThan(PAGE_LOAD_THRESHOLD)
  })

  test('项目列表页在合理时间内加载', async ({ page }) => {
    const start = Date.now()
    await navigateTo(page, '/projects')
    await expect(page.locator('.el-table, .el-empty').first()).toBeVisible({
      timeout: PAGE_LOAD_THRESHOLD,
    })
    const duration = Date.now() - start
    console.log(`项目列表加载耗时: ${duration}ms`)
    expect(duration).toBeLessThan(PAGE_LOAD_THRESHOLD)
  })

  test('路由切换响应迅速', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {})

    // 切换到项目列表
    const start = Date.now()
    await page.goto('/projects')
    await expect(page.locator('.el-table, .el-empty').first()).toBeVisible({
      timeout: PAGE_LOAD_THRESHOLD,
    })
    const duration = Date.now() - start
    console.log(`路由切换耗时: ${duration}ms`)
    expect(duration).toBeLessThan(PAGE_LOAD_THRESHOLD)
  })

  test('帮扶村列表页在合理时间内加载', async ({ page }) => {
    const start = Date.now()
    await navigateTo(page, '/villages')
    await expect(page.locator('.el-table, .el-empty, .village-list').first()).toBeVisible({
      timeout: PAGE_LOAD_THRESHOLD,
    })
    const duration = Date.now() - start
    console.log(`帮扶村列表加载耗时: ${duration}ms`)
    expect(duration).toBeLessThan(PAGE_LOAD_THRESHOLD)
  })
})
