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
        "src/env.d.ts"
      ],
      thresholds: {
        "src/utils/**/*.ts": { statements: 80, branches: 70, functions: 75, lines: 80 },
        "src/stores/**/*.ts": { statements: 70, branches: 60, functions: 55, lines: 70 },
        "src/composables/**/*.ts": { statements: 65, branches: 50, functions: 55, lines: 65 },
        "src/api/**/*.ts": { statements: 70, branches: 60, functions: 55, lines: 70 }
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
export {
  vitest_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZXN0LmNvbmZpZy50cyJdLAogICJzb3VyY2VzQ29udGVudCI6IFsiY29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2Rpcm5hbWUgPSBcIkM6XFxcXG1pbGl0YXJ5LVJ1cmFsIFJldml0YWxpemF0aW9uLXN5c3RlbVxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcbWlsaXRhcnktUnVyYWwgUmV2aXRhbGl6YXRpb24tc3lzdGVtXFxcXGZyb250ZW5kXFxcXHZpdGVzdC5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L21pbGl0YXJ5LVJ1cmFsJTIwUmV2aXRhbGl6YXRpb24tc3lzdGVtL2Zyb250ZW5kL3ZpdGVzdC5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlc3QvY29uZmlnJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgeyBmaWxlVVJMVG9QYXRoIH0gZnJvbSAnbm9kZTp1cmwnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFt2dWUoKV0sXG4gIHRlc3Q6IHtcbiAgICBnbG9iYWxzOiB0cnVlLFxuICAgIGVudmlyb25tZW50OiAnanNkb20nLFxuICAgIHBvb2w6ICd0aHJlYWRzJyxcbiAgICBzaW5nbGVUaHJlYWQ6IHRydWUsXG4gICAgc2V0dXBGaWxlczogWycuL3NyYy90ZXN0L3NldHVwLnRzJ10sXG4gICAgLy8gXHU2MzkyXHU5NjY0RTJFXHU2RDRCXHU4QkQ1XHVGRjA4XHU3NTMxUGxheXdyaWdodFx1OEZEMFx1ODg0Q1x1RkYwOVxuICAgIGV4Y2x1ZGU6IFtcbiAgICAgICcqKi9ub2RlX21vZHVsZXMvKionLFxuICAgICAgJyoqL25vZGVfbW9kdWxlc19vbGQvKionLFxuICAgICAgJyoqL25vZGVfbW9kdWxlc19jb3JydXB0ZWQvKionLFxuICAgICAgJyoqL2Rpc3QvKionLFxuICAgICAgJyoqL3Rlc3RzL2UyZS8qKicsXG4gICAgICAnKiovKi5lMmUudHMnLFxuICAgIF0sXG4gICAgaW5jbHVkZTogW1xuICAgICAgJyoqL3Rlc3RzL3VuaXQvKiovKi50ZXN0LnRzJyxcbiAgICAgICcqKi9zcmMvKiovX190ZXN0c19fLyoqLyouc3BlYy50cydcbiAgICBdLFxuICAgIGNvdmVyYWdlOiB7XG4gICAgICBwcm92aWRlcjogJ3Y4JyxcbiAgICAgIHJlcG9ydGVyOiBbJ3RleHQnLCAnanNvbicsICdodG1sJ10sXG4gICAgICBpbmNsdWRlOiBbXG4gICAgICAgICdzcmMvKiovKi57dHMsdnVlfScsXG4gICAgICBdLFxuICAgICAgZXhjbHVkZTogW1xuICAgICAgICAnbm9kZV9tb2R1bGVzLycsXG4gICAgICAgICdzcmMvdGVzdC8nLFxuICAgICAgICAnKiovKi5kLnRzJyxcbiAgICAgICAgJyoqLyouY29uZmlnLionLFxuICAgICAgICAnKiovLmVzbGludHJjLionLFxuICAgICAgICAnKiovbW9ja0RhdGEnLFxuICAgICAgICAnZGlzdC8nLFxuICAgICAgICAndGVzdHMvZTJlLycsXG4gICAgICAgICdlMmUvKionLFxuICAgICAgICAnc2NyaXB0cy8qKicsXG4gICAgICAgICdzcmMvQXBwLnZ1ZScsXG4gICAgICAgICdzcmMvQXBwLnRlc3QudnVlJyxcbiAgICAgICAgJ3NyYy9tYWluLnRzJyxcbiAgICAgICAgJ3NyYy92aXRlLWVudi5kLnRzJyxcbiAgICAgICAgJ3NyYy9hdXRvLWltcG9ydHMuZC50cycsXG4gICAgICAgICdzcmMvY29tcG9uZW50cy5kLnRzJyxcbiAgICAgICAgJ3NyYy9lbnYuZC50cycsXG4gICAgICBdLFxuICAgICAgdGhyZXNob2xkczoge1xuICAgICAgICAnc3JjL3V0aWxzLyoqLyoudHMnOiB7IHN0YXRlbWVudHM6IDgwLCBicmFuY2hlczogNzAsIGZ1bmN0aW9uczogNzUsIGxpbmVzOiA4MCB9LFxuICAgICAgICAnc3JjL3N0b3Jlcy8qKi8qLnRzJzogeyBzdGF0ZW1lbnRzOiA3MCwgYnJhbmNoZXM6IDYwLCBmdW5jdGlvbnM6IDU1LCBsaW5lczogNzAgfSxcbiAgICAgICAgJ3NyYy9jb21wb3NhYmxlcy8qKi8qLnRzJzogeyBzdGF0ZW1lbnRzOiA2NSwgYnJhbmNoZXM6IDUwLCBmdW5jdGlvbnM6IDU1LCBsaW5lczogNjUgfSxcbiAgICAgICAgJ3NyYy9hcGkvKiovKi50cyc6IHsgc3RhdGVtZW50czogNzAsIGJyYW5jaGVzOiA2MCwgZnVuY3Rpb25zOiA1NSwgbGluZXM6IDcwIH0sXG4gICAgICB9LFxuICAgIH0sXG4gICAgdGVzdFRpbWVvdXQ6IDYwMDAwLFxuICAgIGhvb2tUaW1lb3V0OiA2MDAwMCxcbiAgfSxcbiAgcmVzb2x2ZToge1xuICAgIGFsaWFzOiB7XG4gICAgICAnQCc6IGZpbGVVUkxUb1BhdGgobmV3IFVSTCgnLi9zcmMnLCBpbXBvcnQubWV0YS51cmwpKVxuICAgIH0sXG4gIH0sXG59KVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUE4VSxTQUFTLG9CQUFvQjtBQUMzVyxPQUFPLFNBQVM7QUFDaEIsU0FBUyxxQkFBcUI7QUFGaUwsSUFBTSwyQ0FBMkM7QUFJaFEsSUFBTyx3QkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUyxDQUFDLElBQUksQ0FBQztBQUFBLEVBQ2YsTUFBTTtBQUFBLElBQ0osU0FBUztBQUFBLElBQ1QsYUFBYTtBQUFBLElBQ2IsTUFBTTtBQUFBLElBQ04sY0FBYztBQUFBLElBQ2QsWUFBWSxDQUFDLHFCQUFxQjtBQUFBO0FBQUEsSUFFbEMsU0FBUztBQUFBLE1BQ1A7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLElBQ0Y7QUFBQSxJQUNBLFNBQVM7QUFBQSxNQUNQO0FBQUEsTUFDQTtBQUFBLElBQ0Y7QUFBQSxJQUNBLFVBQVU7QUFBQSxNQUNSLFVBQVU7QUFBQSxNQUNWLFVBQVUsQ0FBQyxRQUFRLFFBQVEsTUFBTTtBQUFBLE1BQ2pDLFNBQVM7QUFBQSxRQUNQO0FBQUEsTUFDRjtBQUFBLE1BQ0EsU0FBUztBQUFBLFFBQ1A7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsUUFDQTtBQUFBLFFBQ0E7QUFBQSxRQUNBO0FBQUEsTUFDRjtBQUFBLE1BQ0EsWUFBWTtBQUFBLFFBQ1YscUJBQXFCLEVBQUUsWUFBWSxJQUFJLFVBQVUsSUFBSSxXQUFXLElBQUksT0FBTyxHQUFHO0FBQUEsUUFDOUUsc0JBQXNCLEVBQUUsWUFBWSxJQUFJLFVBQVUsSUFBSSxXQUFXLElBQUksT0FBTyxHQUFHO0FBQUEsUUFDL0UsMkJBQTJCLEVBQUUsWUFBWSxJQUFJLFVBQVUsSUFBSSxXQUFXLElBQUksT0FBTyxHQUFHO0FBQUEsUUFDcEYsbUJBQW1CLEVBQUUsWUFBWSxJQUFJLFVBQVUsSUFBSSxXQUFXLElBQUksT0FBTyxHQUFHO0FBQUEsTUFDOUU7QUFBQSxJQUNGO0FBQUEsSUFDQSxhQUFhO0FBQUEsSUFDYixhQUFhO0FBQUEsRUFDZjtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxjQUFjLElBQUksSUFBSSxTQUFTLHdDQUFlLENBQUM7QUFBQSxJQUN0RDtBQUFBLEVBQ0Y7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
