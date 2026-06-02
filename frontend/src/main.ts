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

// 一次性将旧版 localStorage token 迁移到 sessionStorage
AuthStorage.migrateFromLocalStorage();

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount("#app");

export default app;