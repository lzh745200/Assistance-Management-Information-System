/**
 * E2E 测试公共辅助函数
 */
import { type Page, expect } from '@playwright/test'

const TEST_USER = {
  username: process.env.TEST_USERNAME || 'admin',
  password: process.env.TEST_PASSWORD || 'Admin@202507!',
}

/**
 * 登录并等待跳转到首页
 */
export async function login(page: Page) {
  await page.goto('/login')
  await page.locator('input[placeholder*="用户名"], input[type="text"]').first().fill(TEST_USER.username)
  await page.locator('input[type="password"]').fill(TEST_USER.password)
  await page.locator('button[type="submit"], button:has-text("登录")').click()
  // 等待登录成功跳转
  await expect(page).toHaveURL(/\/(dashboard|home|$)/, { timeout: 15000 })
}

/**
 * 带重试的导航到指定路由
 */
export async function navigateTo(page: Page, path: string) {
  await page.goto(path)
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {})
}
