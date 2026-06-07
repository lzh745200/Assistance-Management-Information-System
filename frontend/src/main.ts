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
// 多层策略：CSS 样式注入 + JS 拦截 + EP 函数重写
{
  // 策略1：运行时注入 CSS 样式表（优先级最高）
  const styleSheet = new CSSStyleSheet();
  styleSheet.replaceSync(`
    .el-message, .el-message--success, .el-message--error, .el-message--warning, .el-message--info {
      top: 50% !important;
      left: 50% !important;
      right: auto !important;
      bottom: auto !important;
      transform: translate(-50%, -50%) !important;
    }
    .el-notification {
      top: 50% !important;
      left: 50% !important;
      right: auto !important;
      bottom: auto !important;
      transform: translate(-50%, -50%) !important;
      margin: 0 !important;
    }
    .el-message-box {
      position: fixed !important;
      top: 50% !important;
      left: 50% !important;
      transform: translate(-50%, -50%) !important;
    }
  `);
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, styleSheet];

  // 策略2：持续观察并强制居中（EP 可能在创建后重新设 style.top）
  const forceCenter = (el: HTMLElement) => {
    const s = el.style;
    if (s.getPropertyPriority("top") !== "important" || s.top !== "50%") {
      s.setProperty("top", "50%", "important");
      s.setProperty("left", "50%", "important");
      s.setProperty("transform", "translate(-50%, -50%)", "important");
      s.setProperty("margin", "0", "important");
      s.setProperty("right", "auto", "important");
      s.setProperty("bottom", "auto", "important");
    }
  };
  // 首次创建时
  new MutationObserver((ms) => {
    for (const m of ms) for (const n of m.addedNodes) {
      if (n instanceof HTMLElement) {
        if (n.classList.contains("el-message") || n.classList.contains("el-notification")) {
          forceCenter(n);
          // 持续监控：EP 会在 0-200ms 内重新设置 top 用于消息堆叠
          for (const delay of [0, 50, 100, 200]) setTimeout(() => forceCenter(n), delay);
        }
      }
    }
  }).observe(document.body, { childList: true, subtree: true });
}

export default app;
