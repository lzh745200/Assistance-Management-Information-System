/**
 * 懒加载组件 Composable
 */
import { defineAsyncComponent, type Component } from "vue";

export function useLazyComponent() {
  function loadComponent(
    loader: () => Promise<{ default: Component }>,
    loadingComponent?: Component,
    delay = 200,
  ) {
    return defineAsyncComponent({
      loader,
      loadingComponent,
      delay,
    });
  }

  return { loadComponent };
}