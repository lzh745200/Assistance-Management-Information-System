import { defineConfig } from 'vitest/config'
import base from './vitest.config'

export default defineConfig({
  ...base,
  cacheDir: 'C:/Users/Administrator/AppData/Local/Temp/opencode/vite-cache-isolated',
  test: {
    ...base.test,
    cacheDir: 'C:/Users/Administrator/AppData/Local/Temp/opencode/vitest-cache-isolated2',
  },
})
