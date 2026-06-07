/**
 * 应用入口 main.ts
 *
 * Element Plus 组件由 unplugin-vue-components 按需自动导入。
 * 如需使用 ElMessage/ElMessageBox 等命令式 API，从 element-plus 单独导入。
 */

// ── 第零层：DOM 级 CSS 注入，确保所有弹出层绝对居中（优先级高于任何外部 CSS）──
const _style = document.createElement("style");
_style.textContent = `
  .el-message,.el-message--success,.el-message--error,.el-message--warning,.el-message--info{top:50%!important;left:50%!important;right:auto!important;bottom:auto!important;transform:translate(-50%,-50%)!important;position:fixed!important}
  .el-notification{top:50%!important;left:50%!important;right:auto!important;bottom:auto!important;transform:translate(-50%,-50%)!important;position:fixed!important;margin:0!important}
  .el-notification__group{top:0!important;left:0!important;right:0!important;bottom:0!important;display:flex!important;align-items:center!important;justify-content:center!important}
  .el-message-box{top:50%!important;left:50%!important;transform:translate(-50%,-50%)!important;position:fixed!important;margin:0!important}
`;
document.head.appendChild(_style);

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

export default app;
