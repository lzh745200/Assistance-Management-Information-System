import { defineConfig } from 'vitest/config'
import base from './vitest.config'

export default defineConfig({
  ...base,
  test: {
    ...base.test,
    cacheDir: 'C:/Users/Administrator/AppData/Local/Temp/opencode/vitest-cache-shared',
  },
})
