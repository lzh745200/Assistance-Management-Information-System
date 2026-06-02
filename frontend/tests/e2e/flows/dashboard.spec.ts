/**
 * Dashboard（工作台）E2E 测试
 *
 * 重点覆盖：
 * - 页面正确加载
 * - 核心统计指标展示
 * - 快捷导航可用
 * - 项目进度表格
 * - 经费概况
 */
import { test, expect } from '@playwright/test'
import { login, navigateTo } from '../helpers'

test.describe('工作台 Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('页面正确加载 - 展示欢迎横幅', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 欢迎横幅
    await expect(page.locator('.welcome-banner, .dashboard-page')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.welcome-title, h2')).toContainText('欢迎')
  })

  test('核心统计指标展示', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 统计卡片区域
    const statsGrid = page.locator('.stats-grid, .stat-card').first()
    await expect(statsGrid).toBeVisible({ timeout: 10000 })
    // 至少有3个统计卡片
    const cardCount = await page.locator('.stat-card').count()
    expect(cardCount).toBeGreaterThanOrEqual(3)
  })

  test('快捷导航功能可用', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 快捷导航区域
    const navGrid = page.locator('.nav-grid, .quick-actions')
    await expect(navGrid).toBeVisible({ timeout: 10000 })

    // 点击"新建项目"快捷按钮
    const createBtn = page.locator('button:has-text("新建项目"), .action-btn:has-text("新建项目")')
    if (await createBtn.isVisible()) {
      await createBtn.click()
      await expect(page).toHaveURL(/\/projects\/create/, { timeout: 5000 })
    }
  })

  test('项目进度表格展示', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 项目进度区块
    const projectSection = page.locator('text=项目进度').first()
    await expect(projectSection).toBeVisible({ timeout: 10000 })

    // 表格或空状态
    const hasTable = await page.locator('.data-table, .el-table').isVisible().catch(() => false)
    const hasEmpty = await page.locator('.el-empty, text=暂无数据').isVisible().catch(() => false)
    expect(hasTable || hasEmpty).toBeTruthy()
  })

  test('经费概况展示', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 经费概况区块
    const fundSection = page.locator('text=经费概况').first()
    await expect(fundSection).toBeVisible({ timeout: 10000 })

    // 经费统计数字
    const fundValues = page.locator('.fund-value, .fund-summary-item .fund-value')
    const count = await fundValues.count()
    expect(count).toBeGreaterThanOrEqual(2)
  })

  test('近期动态展示', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 近期动态区块
    const activitySection = page.locator('text=近期动态').first()
    await expect(activitySection).toBeVisible({ timeout: 10000 })
  })

  test('待办事项功能', async ({ page }) => {
    await navigateTo(page, '/dashboard')
    // 待办事项区块
    const todoSection = page.locator('text=待办事项').first()
    await expect(todoSection).toBeVisible({ timeout: 10000 })

    // 输入框存在
    const input = page.locator('.task-input, input[placeholder*="待办"]')
    await expect(input).toBeVisible()
  })
})
