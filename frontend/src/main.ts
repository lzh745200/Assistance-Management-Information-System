/**
 * 应用入口 main.ts
 *
 * Element Plus 组件由 unplugin-vue-components 按需自动导入。
 * 如需使用 ElMessage/ElMessageBox 等命令式 API，从 element-plus 单独导入。
 */
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./router/guards";
import { AuthStorage } from "@/utils/authStorage";

// 全局样式（Element Plus 覆盖 + 通知居中 + 组件美化）
import "@/styles/index.scss";
// Dashboard 深度视觉主题（注：tokens.scss 通过 vite additionalData 自动注入组件 SCSS 块）
import "@/styles/dashboard-theme.scss";
// 列表页统一规范化 (Phase 2)
import "@/styles/components/list-page.scss";
// 表单/详情页统一升级 (Phase 3)
import "@/styles/components/form-page.scss";

// 一次性将旧版 localStorage token 迁移到 sessionStorage
AuthStorage.migrateFromLocalStorage();

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount("#app");

// ── 全局修复：所有 ElMessage / ElNotification 强制页面正中央 ──
// Element Plus 用 JS 动态设置 style.top/left，CSS !important 有时不生效。
// 使用 MutationObserver 在元素挂载后立即重新定位。
{
  const centerEl = (el: HTMLElement) => {
    el.style.setProperty("top", "50%", "important");
    el.style.setProperty("left", "50%", "important");
    el.style.setProperty("right", "auto", "important");
    el.style.setProperty("bottom", "auto", "important");
    el.style.setProperty("transform", "translate(-50%, -50%)", "important");
    el.style.setProperty("margin", "0", "important");
  };
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      for (const node of m.addedNodes) {
        if (node instanceof HTMLElement) {
          if (node.classList.contains("el-message")) centerEl(node);
          if (node.classList.contains("el-notification")) centerEl(node);
          // 也检查子元素
          node.querySelectorAll?.(".el-message, .el-notification").forEach((c) => centerEl(c as HTMLElement));
        }
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
}

export default app;
