// vitest.isolated.config.ts
import { defineConfig as defineConfig2 } from "file:///C:/military-Rural%20Revitalization-system/frontend/node_modules/vitest/dist/config.js";

// vitest.config.ts
import { defineConfig } from "file:///C:/military-Rural%20Revitalization-system/frontend/node_modules/vitest/dist/config.js";
import vue from "file:///C:/military-Rural%20Revitalization-system/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { fileURLToPath } from "node:url";
var __vite_injected_original_import_meta_url = "file:///C:/military-Rural%20Revitalization-system/frontend/vitest.config.ts";
var vitest_config_default = defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: "jsdom",
    pool: "threads",
    singleThread: true,
    setupFiles: ["./src/test/setup.ts"],
    // 排除E2E测试（由Playwright运行）
    exclude: [
      "**/node_modules/**",
      "**/node_modules_old/**",
      "**/node_modules_corrupted/**",
      "**/dist/**",
      "**/tests/e2e/**",
      "**/*.e2e.ts"
    ],
    include: [
      "**/tests/unit/**/*.test.ts",
      "**/src/**/__tests__/**/*.spec.ts"
    ],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: [
        "src/**/*.{ts,vue}"
      ],
      exclude: [
        "node_modules/",
        "src/test/",
        "**/*.d.ts",
        "**/*.config.*",
        "**/.eslintrc.*",
        "**/mockData",
        "dist/",
        "tests/e2e/",
        "e2e/**",
        "scripts/**",
        "src/App.vue",
        "src/App.test.vue",
        "src/main.ts",
        "src/vite-env.d.ts",
        "src/auto-imports.d.ts",
        "src/components.d.ts",
        "src/env.d.ts",
        // 纯类型定义文件（仅 interface/type，无可执行语句，v8 计数为测量噪音）
        "src/types/analytics.ts",
        "src/types/api.ts",
        "src/types/components.ts",
        "src/types/entities.ts",
        "src/types/helpProject.ts",
        "src/types/index.ts",
        "src/types/models.ts",
        "src/types/organization.ts",
        "src/types/policy.ts"
      ],
      thresholds: {
        "src/utils/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/stores/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/composables/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/api/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/views/**/*.vue": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/components/**/*.vue": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/router/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/config/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 },
        "src/directives/**/*.ts": { statements: 100, branches: 100, functions: 100, lines: 100 }
      }
    },
    testTimeout: 6e4,
    hookTimeout: 6e4
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url))
    }
  }
});

// vitest.isolated.config.ts
var vitest_isolated_config_default = defineConfig2({
  ...vitest_config_default,
  test: {
    ...vitest_config_default.test,
    cacheDir: "C:/Users/Administrator/AppData/Local/Temp/opencode/vitest-cache-shared"
  }
});
export {
  vitest_isolated_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZXN0Lmlzb2xhdGVkLmNvbmZpZy50cyIsICJ2aXRlc3QuY29uZmlnLnRzIl0sCiAgInNvdXJjZXNDb250ZW50IjogWyJjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZGlybmFtZSA9IFwiQzpcXFxcbWlsaXRhcnktUnVyYWwgUmV2aXRhbGl6YXRpb24tc3lzdGVtXFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxtaWxpdGFyeS1SdXJhbCBSZXZpdGFsaXphdGlvbi1zeXN0ZW1cXFxcZnJvbnRlbmRcXFxcdml0ZXN0Lmlzb2xhdGVkLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vQzovbWlsaXRhcnktUnVyYWwlMjBSZXZpdGFsaXphdGlvbi1zeXN0ZW0vZnJvbnRlbmQvdml0ZXN0Lmlzb2xhdGVkLmNvbmZpZy50c1wiO2ltcG9ydCB7IGRlZmluZUNvbmZpZyB9IGZyb20gJ3ZpdGVzdC9jb25maWcnXG5pbXBvcnQgYmFzZSBmcm9tICcuL3ZpdGVzdC5jb25maWcnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIC4uLmJhc2UsXG4gIHRlc3Q6IHtcbiAgICAuLi5iYXNlLnRlc3QsXG4gICAgY2FjaGVEaXI6ICdDOi9Vc2Vycy9BZG1pbmlzdHJhdG9yL0FwcERhdGEvTG9jYWwvVGVtcC9vcGVuY29kZS92aXRlc3QtY2FjaGUtc2hhcmVkJyxcbiAgfSxcbn0pXG4iLCAiY29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2Rpcm5hbWUgPSBcIkM6XFxcXG1pbGl0YXJ5LVJ1cmFsIFJldml0YWxpemF0aW9uLXN5c3RlbVxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcbWlsaXRhcnktUnVyYWwgUmV2aXRhbGl6YXRpb24tc3lzdGVtXFxcXGZyb250ZW5kXFxcXHZpdGVzdC5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L21pbGl0YXJ5LVJ1cmFsJTIwUmV2aXRhbGl6YXRpb24tc3lzdGVtL2Zyb250ZW5kL3ZpdGVzdC5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlc3QvY29uZmlnJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgeyBmaWxlVVJMVG9QYXRoIH0gZnJvbSAnbm9kZTp1cmwnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFt2dWUoKV0sXG4gIHRlc3Q6IHtcbiAgICBnbG9iYWxzOiB0cnVlLFxuICAgIGVudmlyb25tZW50OiAnanNkb20nLFxuICAgIHBvb2w6ICd0aHJlYWRzJyxcbiAgICBzaW5nbGVUaHJlYWQ6IHRydWUsXG4gICAgc2V0dXBGaWxlczogWycuL3NyYy90ZXN0L3NldHVwLnRzJ10sXG4gICAgLy8gXHU2MzkyXHU5NjY0RTJFXHU2RDRCXHU4QkQ1XHVGRjA4XHU3NTMxUGxheXdyaWdodFx1OEZEMFx1ODg0Q1x1RkYwOVxuICAgIGV4Y2x1ZGU6IFtcbiAgICAgICcqKi9ub2RlX21vZHVsZXMvKionLFxuICAgICAgJyoqL25vZGVfbW9kdWxlc19vbGQvKionLFxuICAgICAgJyoqL25vZGVfbW9kdWxlc19jb3JydXB0ZWQvKionLFxuICAgICAgJyoqL2Rpc3QvKionLFxuICAgICAgJyoqL3Rlc3RzL2UyZS8qKicsXG4gICAgICAnKiovKi5lMmUudHMnLFxuICAgIF0sXG4gICAgaW5jbHVkZTogW1xuICAgICAgJyoqL3Rlc3RzL3VuaXQvKiovKi50ZXN0LnRzJyxcbiAgICAgICcqKi9zcmMvKiovX190ZXN0c19fLyoqLyouc3BlYy50cydcbiAgICBdLFxuICAgIGNvdmVyYWdlOiB7XG4gICAgICBwcm92aWRlcjogJ3Y4JyxcbiAgICAgIHJlcG9ydGVyOiBbJ3RleHQnLCAnanNvbicsICdodG1sJ10sXG4gICAgICBpbmNsdWRlOiBbXG4gICAgICAgICdzcmMvKiovKi57dHMsdnVlfScsXG4gICAgICBdLFxuICAgICAgZXhjbHVkZTogW1xuICAgICAgICAnbm9kZV9tb2R1bGVzLycsXG4gICAgICAgICdzcmMvdGVzdC8nLFxuICAgICAgICAnKiovKi5kLnRzJyxcbiAgICAgICAgJyoqLyouY29uZmlnLionLFxuICAgICAgICAnKiovLmVzbGludHJjLionLFxuICAgICAgICAnKiovbW9ja0RhdGEnLFxuICAgICAgICAnZGlzdC8nLFxuICAgICAgICAndGVzdHMvZTJlLycsXG4gICAgICAgICdlMmUvKionLFxuICAgICAgICAnc2NyaXB0cy8qKicsXG4gICAgICAgICdzcmMvQXBwLnZ1ZScsXG4gICAgICAgICdzcmMvQXBwLnRlc3QudnVlJyxcbiAgICAgICAgJ3NyYy9tYWluLnRzJyxcbiAgICAgICAgJ3NyYy92aXRlLWVudi5kLnRzJyxcbiAgICAgICAgJ3NyYy9hdXRvLWltcG9ydHMuZC50cycsXG4gICAgICAgICdzcmMvY29tcG9uZW50cy5kLnRzJyxcbiAgICAgICAgJ3NyYy9lbnYuZC50cycsXG4gICAgICAgIC8vIFx1N0VBRlx1N0M3Qlx1NTc4Qlx1NUI5QVx1NEU0OVx1NjU4N1x1NEVGNlx1RkYwOFx1NEVDNSBpbnRlcmZhY2UvdHlwZVx1RkYwQ1x1NjVFMFx1NTNFRlx1NjI2N1x1ODg0Q1x1OEJFRFx1NTNFNVx1RkYwQ3Y4IFx1OEJBMVx1NjU3MFx1NEUzQVx1NkQ0Qlx1OTFDRlx1NTY2QVx1OTdGM1x1RkYwOVxuICAgICAgICAnc3JjL3R5cGVzL2FuYWx5dGljcy50cycsXG4gICAgICAgICdzcmMvdHlwZXMvYXBpLnRzJyxcbiAgICAgICAgJ3NyYy90eXBlcy9jb21wb25lbnRzLnRzJyxcbiAgICAgICAgJ3NyYy90eXBlcy9lbnRpdGllcy50cycsXG4gICAgICAgICdzcmMvdHlwZXMvaGVscFByb2plY3QudHMnLFxuICAgICAgICAnc3JjL3R5cGVzL2luZGV4LnRzJyxcbiAgICAgICAgJ3NyYy90eXBlcy9tb2RlbHMudHMnLFxuICAgICAgICAnc3JjL3R5cGVzL29yZ2FuaXphdGlvbi50cycsXG4gICAgICAgICdzcmMvdHlwZXMvcG9saWN5LnRzJyxcbiAgICAgIF0sXG4gICAgICB0aHJlc2hvbGRzOiB7XG4gICAgICAgICdzcmMvdXRpbHMvKiovKi50cyc6IHsgc3RhdGVtZW50czogMTAwLCBicmFuY2hlczogMTAwLCBmdW5jdGlvbnM6IDEwMCwgbGluZXM6IDEwMCB9LFxuICAgICAgICAnc3JjL3N0b3Jlcy8qKi8qLnRzJzogeyBzdGF0ZW1lbnRzOiAxMDAsIGJyYW5jaGVzOiAxMDAsIGZ1bmN0aW9uczogMTAwLCBsaW5lczogMTAwIH0sXG4gICAgICAgICdzcmMvY29tcG9zYWJsZXMvKiovKi50cyc6IHsgc3RhdGVtZW50czogMTAwLCBicmFuY2hlczogMTAwLCBmdW5jdGlvbnM6IDEwMCwgbGluZXM6IDEwMCB9LFxuICAgICAgICAnc3JjL2FwaS8qKi8qLnRzJzogeyBzdGF0ZW1lbnRzOiAxMDAsIGJyYW5jaGVzOiAxMDAsIGZ1bmN0aW9uczogMTAwLCBsaW5lczogMTAwIH0sXG4gICAgICAgICdzcmMvdmlld3MvKiovKi52dWUnOiB7IHN0YXRlbWVudHM6IDEwMCwgYnJhbmNoZXM6IDEwMCwgZnVuY3Rpb25zOiAxMDAsIGxpbmVzOiAxMDAgfSxcbiAgICAgICAgJ3NyYy9jb21wb25lbnRzLyoqLyoudnVlJzogeyBzdGF0ZW1lbnRzOiAxMDAsIGJyYW5jaGVzOiAxMDAsIGZ1bmN0aW9uczogMTAwLCBsaW5lczogMTAwIH0sXG4gICAgICAgICdzcmMvcm91dGVyLyoqLyoudHMnOiB7IHN0YXRlbWVudHM6IDEwMCwgYnJhbmNoZXM6IDEwMCwgZnVuY3Rpb25zOiAxMDAsIGxpbmVzOiAxMDAgfSxcbiAgICAgICAgJ3NyYy9jb25maWcvKiovKi50cyc6IHsgc3RhdGVtZW50czogMTAwLCBicmFuY2hlczogMTAwLCBmdW5jdGlvbnM6IDEwMCwgbGluZXM6IDEwMCB9LFxuICAgICAgICAnc3JjL2RpcmVjdGl2ZXMvKiovKi50cyc6IHsgc3RhdGVtZW50czogMTAwLCBicmFuY2hlczogMTAwLCBmdW5jdGlvbnM6IDEwMCwgbGluZXM6IDEwMCB9LFxuICAgICAgfSxcbiAgICB9LFxuICAgIHRlc3RUaW1lb3V0OiA2MDAwMCxcbiAgICBob29rVGltZW91dDogNjAwMDAsXG4gIH0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgJ0AnOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vc3JjJywgaW1wb3J0Lm1ldGEudXJsKSlcbiAgICB9LFxuICB9LFxufSlcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBZ1csU0FBUyxnQkFBQUEscUJBQW9COzs7QUNBL0MsU0FBUyxvQkFBb0I7QUFDM1csT0FBTyxTQUFTO0FBQ2hCLFNBQVMscUJBQXFCO0FBRmlMLElBQU0sMkNBQTJDO0FBSWhRLElBQU8sd0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxJQUFJLENBQUM7QUFBQSxFQUNmLE1BQU07QUFBQSxJQUNKLFNBQVM7QUFBQSxJQUNULGFBQWE7QUFBQSxJQUNiLE1BQU07QUFBQSxJQUNOLGNBQWM7QUFBQSxJQUNkLFlBQVksQ0FBQyxxQkFBcUI7QUFBQTtBQUFBLElBRWxDLFNBQVM7QUFBQSxNQUNQO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxJQUNGO0FBQUEsSUFDQSxTQUFTO0FBQUEsTUFDUDtBQUFBLE1BQ0E7QUFBQSxJQUNGO0FBQUEsSUFDQSxVQUFVO0FBQUEsTUFDUixVQUFVO0FBQUEsTUFDVixVQUFVLENBQUMsUUFBUSxRQUFRLE1BQU07QUFBQSxNQUNqQyxTQUFTO0FBQUEsUUFDUDtBQUFBLE1BQ0Y7QUFBQSxNQUNBLFNBQVM7QUFBQSxRQUNQO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBO0FBQUEsUUFFQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsTUFDRjtBQUFBLE1BQ0EsWUFBWTtBQUFBLFFBQ1YscUJBQXFCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDbEYsc0JBQXNCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDbkYsMkJBQTJCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDeEYsbUJBQW1CLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDaEYsc0JBQXNCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDbkYsMkJBQTJCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDeEYsc0JBQXNCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDbkYsc0JBQXNCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsUUFDbkYsMEJBQTBCLEVBQUUsWUFBWSxLQUFLLFVBQVUsS0FBSyxXQUFXLEtBQUssT0FBTyxJQUFJO0FBQUEsTUFDekY7QUFBQSxJQUNGO0FBQUEsSUFDQSxhQUFhO0FBQUEsSUFDYixhQUFhO0FBQUEsRUFDZjtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxjQUFjLElBQUksSUFBSSxTQUFTLHdDQUFlLENBQUM7QUFBQSxJQUN0RDtBQUFBLEVBQ0Y7QUFDRixDQUFDOzs7QUQ3RUQsSUFBTyxpQ0FBUUMsY0FBYTtBQUFBLEVBQzFCLEdBQUc7QUFBQSxFQUNILE1BQU07QUFBQSxJQUNKLEdBQUcsc0JBQUs7QUFBQSxJQUNSLFVBQVU7QUFBQSxFQUNaO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFsiZGVmaW5lQ29uZmlnIiwgImRlZmluZUNvbmZpZyJdCn0K
