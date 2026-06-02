import { useRouter } from "vue-router";
import type { RouteLocationRaw } from "vue-router";

function getPathString(path: string | RouteLocationRaw): string | undefined {
  return typeof path === "string" ? path : path.path;
}

/**
 * 安全的路由导航工具
 * 提供带错误处理和回退机制的路由跳转功能
 */
export function useRouterSafe() {
  const router = useRouter();

  /**
   * 安全地跳转到指定路由
   * 如果 Vue Router 跳转失败，会回退到原生页面跳转
   *
   * @param path - 目标路由路径或路由对象
   * @param debugLabel - 可选的调试标签，仅在开发环境输出日志
   */
  const pushSafe = (path: string | RouteLocationRaw, debugLabel?: string) => {
    const pathString = getPathString(path);

    try {
      if (debugLabel && import.meta.env.DEV) {
        console.log(`尝试跳转到${debugLabel}页面`);
      }

      router.push(path).catch((err) => {
        console.error("路由跳转失败:", err);
        if (pathString) {
          window.location.href = pathString;
        }
      });
    } catch (error) {
      console.error("跳转异常:", error);
      if (pathString) {
        window.location.href = pathString;
      }
    }
  };

  return { pushSafe };
}
