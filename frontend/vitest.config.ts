import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    pool: 'threads',
    singleThread: true,
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
      include: [
        'src/**/*.{ts,vue}',
      ],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/.eslintrc.*',
        '**/mockData',
        'dist/',
        'tests/e2e/',
        'e2e/**',
        'scripts/**',
        'src/App.vue',
        'src/App.test.vue',
        'src/main.ts',
        'src/vite-env.d.ts',
        'src/auto-imports.d.ts',
        'src/components.d.ts',
        'src/env.d.ts',
      ],
      thresholds: {
        'src/utils/**/*.ts': { statements: 80, branches: 70, functions: 75, lines: 80 },
        'src/stores/**/*.ts': { statements: 70, branches: 60, functions: 55, lines: 70 },
        'src/composables/**/*.ts': { statements: 65, branches: 50, functions: 55, lines: 65 },
        'src/api/**/*.ts': { statements: 70, branches: 60, functions: 55, lines: 70 },
      },
    },
    testTimeout: 60000,
    hookTimeout: 60000,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
