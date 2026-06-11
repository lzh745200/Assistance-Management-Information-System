/**
 * ElNotification 全局默认值包装器
 *
 * Element Plus 2.x 的 ElNotification 没有全局 defaults 机制（无 notificationDefaults 对象）。
 * 此模块包装 ElNotification，注入全局默认值：显示关闭按钮 + 5s 自动关闭。
 *
 * 使用方式:
 *   import { notify } from '@/utils/notify';
 *   notify({ type: 'error', title: '错误', message: '...' });
 *   notify.success('操作成功'); // 类型快捷方式
 */

import { ElNotification } from "element-plus";
import type { NotificationParams, NotificationParamsTyped } from "element-plus";

/** 全局默认值：显示关闭按钮 + 5s 自动关闭（对齐 ElMessage messageDefaults） */
const GLOBAL_DEFAULTS: Partial<NotificationParamsTyped> = {
  showClose: true,
  duration: 5000,
};

/** 包装后的通知函数，自动合并全局默认值 */
function notify(
  options?: NotificationParams,
): ReturnType<typeof ElNotification> {
  if (typeof options === "string") {
    return ElNotification({ ...GLOBAL_DEFAULTS, message: options });
  }
  return ElNotification({ ...GLOBAL_DEFAULTS, ...options });
}

// 类型快捷方式（success / error / warning / info）
notify.success = (
  options?: NotificationParams,
): ReturnType<typeof ElNotification> => {
  if (typeof options === "string") {
    return ElNotification.success({ ...GLOBAL_DEFAULTS, message: options });
  }
  return ElNotification.success({ ...GLOBAL_DEFAULTS, ...options });
};

notify.error = (
  options?: NotificationParams,
): ReturnType<typeof ElNotification> => {
  if (typeof options === "string") {
    return ElNotification.error({ ...GLOBAL_DEFAULTS, message: options });
  }
  return ElNotification.error({ ...GLOBAL_DEFAULTS, ...options });
};

notify.warning = (
  options?: NotificationParams,
): ReturnType<typeof ElNotification> => {
  if (typeof options === "string") {
    return ElNotification.warning({ ...GLOBAL_DEFAULTS, message: options });
  }
  return ElNotification.warning({ ...GLOBAL_DEFAULTS, ...options });
};

notify.info = (
  options?: NotificationParams,
): ReturnType<typeof ElNotification> => {
  if (typeof options === "string") {
    return ElNotification.info({ ...GLOBAL_DEFAULTS, message: options });
  }
  return ElNotification.info({ ...GLOBAL_DEFAULTS, ...options });
};

notify.closeAll = ElNotification.closeAll;

export { notify };
export default notify;
