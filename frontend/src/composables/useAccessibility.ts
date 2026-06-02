import { ref, type Ref } from "vue";

/**
 * 焦点陷阱组合式函数
 * 用于模态框、对话框等需要限制焦点在容器内的场景
 */
export function useFocusTrap(containerRef: Ref<HTMLElement | null>) {
  const previousActiveElement = ref<HTMLElement | null>(null);

  const getFocusableElements = (): HTMLElement[] => {
    const container = containerRef.value;
    if (!container) return [];

    return Array.from(
      container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      ),
    ).filter(
      (el) => !el.hasAttribute("disabled") && !el.getAttribute("aria-hidden"),
    ) as HTMLElement[];
  };

  const trapFocus = (event: KeyboardEvent) => {
    if (event.key !== "Tab" || !containerRef.value) return;

    const focusableElements = getFocusableElements();
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        event.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        event.preventDefault();
      }
    }
  };

  const activate = () => {
    previousActiveElement.value = document.activeElement as HTMLElement;
    const focusableElements = getFocusableElements();
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
    document.addEventListener("keydown", trapFocus);
  };

  const deactivate = () => {
    document.removeEventListener("keydown", trapFocus);
    if (previousActiveElement.value) {
      previousActiveElement.value.focus();
    }
  };

  return {
    activate,
    deactivate,
    getFocusableElements,
  };
}

/**
 * 页面标题管理
 * 用于无障碍阅读器识别当前页面
 */
export function usePageTitle() {
  const setPageTitle = (title: string) => {
    document.title = `${title} - 帮扶管理信息系统`;
    // 设置 aria-live 区域通知屏幕阅读器
    const liveRegion = document.getElementById("page-title-live-region");
    if (liveRegion) {
      liveRegion.textContent = `已导航到: ${title}`;
    }
  };

  return { setPageTitle };
}

/**
 * 跳过链接（Skip Link）
 * 为键盘用户提供跳转到主要内容的快捷方式
 */
export function useSkipLink() {
  const skipToMainContent = () => {
    const mainContent = document.querySelector(
      'main, [role="main"], #main-content',
    );
    if (mainContent) {
      (mainContent as HTMLElement).focus();
      (mainContent as HTMLElement).scrollIntoView({ behavior: "smooth" });
    }
  };

  return { skipToMainContent };
}

/**
 * 表单可访问性增强
 */
export function useAccessibleForm() {
  /**
   * 生成唯一的ID
   */
  const generateId = (prefix = "form"): string => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  };

  /**
   * 验证并报告表单字段错误
   */
  const reportFieldError = (fieldId: string, errorMessage: string) => {
    const field = document.getElementById(fieldId);
    const errorId = `${fieldId}-error`;

    if (field) {
      field.setAttribute("aria-invalid", "true");
      field.setAttribute("aria-describedby", errorId);
    }

    // 更新或创建错误信息元素
    let errorElement = document.getElementById(errorId);
    if (!errorElement) {
      errorElement = document.createElement("div");
      errorElement.id = errorId;
      errorElement.className = "form-error";
      field?.parentNode?.appendChild(errorElement);
    }
    errorElement.textContent = errorMessage;
    errorElement.setAttribute("role", "alert");
  };

  /**
   * 清除字段错误
   */
  const clearFieldError = (fieldId: string) => {
    const field = document.getElementById(fieldId);
    if (field) {
      field.removeAttribute("aria-invalid");
      field.removeAttribute("aria-describedby");
    }

    const errorId = `${fieldId}-error`;
    const errorElement = document.getElementById(errorId);
    if (errorElement) {
      errorElement.remove();
    }
  };

  return {
    generateId,
    reportFieldError,
    clearFieldError,
  };
}

/**
 * 通知/提示可访问性
 */
export function useAccessibleNotification() {
  const announce = (
    message: string,
    priority: "polite" | "assertive" = "polite",
  ) => {
    const liveRegion = document.getElementById(`live-region-${priority}`);
    if (liveRegion) {
      liveRegion.textContent = message;
      // 清空以便下次通知
      setTimeout(() => {
        liveRegion.textContent = "";
      }, 1000);
    }
  };

  return { announce };
}
