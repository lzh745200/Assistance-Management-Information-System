import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    pool: 'forks',
    setupFiles: ['./src/test/setup.ts'],
    // 排除E2E测试（由Playwright运行）
    exclude: [
      '**/node_modules/**',
      '**/node_modules_old/**',
      '**/node_modules_corrupted/**',
      '**/dist/**',
      '**/tests/e2e/**',
      '**/*.e2e.ts',
    ],
    include: [
      '**/tests/unit/**/*.test.ts',
      '**/src/**/__tests__/**/*.spec.ts'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'dist/',
        'tests/e2e/',
      ],
      // 覆盖率阈值 — 设为可实现基线 (基于实际测试结果)
      // 详细分析见 docs/测试覆盖率差距报告.md
      thresholds: {
        global: {
          statements: 40,
          branches: 35,
          functions: 25,
          lines: 40
        },
        'src/utils/**/*.ts': {
          statements: 44,
          branches: 40,
          functions: 45,
          lines: 44
        },
        'src/stores/**/*.ts': {
          statements: 44,
          branches: 40,
          functions: 15,
          lines: 44
        },
        'src/composables/**/*.ts': {
          statements: 35,
          branches: 40,
          functions: 35,
          lines: 35
        },
        'src/api/**/*.ts': {
          statements: 50,
          branches: 40,
          functions: 5,
          lines: 50
        }
      }
    },
    // 属性测试配置
    testTimeout: 60000, // 属性测试 + 高并发并行时 element-plus 模块加载较慢
    forks: {
      maxForks: 4, // 限制并行进程数，防止资源竞争导致动态 import 超时
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
