/**
 * 离线模式工具
 * 单机版系统默认离线运行
 */

/** 检查是否处于离线模式 */
export function isOfflineMode(): boolean {
  return !navigator.onLine || localStorage.getItem("offline_mode") === "true";
}

/** 设置离线模式 */
export function setOfflineMode(offline: boolean): void {
  localStorage.setItem("offline_mode", String(offline));
}

/** 监听网络状态变化 */
export function onNetworkChange(
  callback: (online: boolean) => void,
): () => void {
  const onOnline = () => callback(true);
  const onOffline = () => callback(false);

  window.addEventListener("online", onOnline);
  window.addEventListener("offline", onOffline);

  return () => {
    window.removeEventListener("online", onOnline);
    window.removeEventListener("offline", onOffline);
  };
}

export default {
  isOfflineMode,
  setOfflineMode,
  onNetworkChange,
};
