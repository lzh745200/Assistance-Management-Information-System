/**
 * 前端性能优化工具
 *
 * 包含：
 * - 资源预加载
 * - 图片懒加载
 * - 关键资源优先级
 * - 性能监控
 *
 * 需求: 10.5
 */

import { logger } from "@/utils/logger";
import {
  defineAsyncComponent,
  type Component,
  type AsyncComponentLoader,
} from "vue";
import { ElSkeleton } from "element-plus";

/**
 * 资源预加载类型
 */
export type PreloadType = "script" | "style" | "image" | "font" | "fetch";

/**
 * 预加载配置
 */
export interface PreloadConfig {
  href: string;
  as: PreloadType;
  type?: string;
  crossOrigin?: "anonymous" | "use-credentials";
  media?: string;
}

/**
 * 异步组件配置
 */
export interface AsyncComponentConfig {
  /** 加载超时时间（毫秒） */
  timeout?: number;
  /** 加载延迟时间（毫秒） */
  delay?: number;
  /** 是否显示加载状态 */
  showLoading?: boolean;
  /** 加载失败时的重试次数 */
  retryCount?: number;
}

// 默认异步组件配置
const DEFAULT_ASYNC_CONFIG: Required<AsyncComponentConfig> = {
  timeout: 30000,
  delay: 200,
  showLoading: true,
  retryCount: 3,
};

/**
 * 创建带加载状态的异步组件
 * @param loader 组件加载函数
 * @param config 配置选项
 */
export function createAsyncComponent(
  loader: AsyncComponentLoader,
  config: AsyncComponentConfig = {},
): Component {
  const mergedConfig = { ...DEFAULT_ASYNC_CONFIG, ...config };
  let retryCount = 0;

  const retryLoader: AsyncComponentLoader = async () => {
    try {
      return await loader();
    } catch (error) {
      if (retryCount < mergedConfig.retryCount) {
        retryCount++;
        logger.warn(
          `[AsyncComponent] 加载失败，正在重试 (${retryCount}/${mergedConfig.retryCount})`,
        );
        return retryLoader();
      }
      throw error;
    }
  };

  return defineAsyncComponent({
    loader: retryLoader,
    loadingComponent: mergedConfig.showLoading ? ElSkeleton : undefined,
    delay: mergedConfig.delay,
    timeout: mergedConfig.timeout,
    onError(error, retry, fail, attempts) {
      if (attempts <= mergedConfig.retryCount) {
        logger.warn(
          `[AsyncComponent] 加载错误，尝试重试 (${attempts}/${mergedConfig.retryCount})`,
        );
        retry();
      } else {
        logger.error("[AsyncComponent] 加载失败:", error);
        fail();
      }
    },
  });
}

/**
 * 预加载资源
 * @param config 预加载配置
 */
export function preloadResource(config: PreloadConfig): HTMLLinkElement {
  const link = document.createElement("link");
  link.rel = "preload";
  link.href = config.href;
  link.as = config.as;

  if (config.type) {
    link.type = config.type;
  }

  if (config.crossOrigin) {
    link.crossOrigin = config.crossOrigin;
  }

  if (config.media) {
    link.media = config.media;
  }

  document.head.appendChild(link);
  return link;
}

/**
 * 预获取资源（低优先级）
 * @param href 资源地址
 */
export function prefetchResource(href: string): HTMLLinkElement {
  const link = document.createElement("link");
  link.rel = "prefetch";
  link.href = href;
  document.head.appendChild(link);
  return link;
}

/**
 * DNS 预解析
 * @param domain 域名
 */
export function dnsPrefetch(domain: string): HTMLLinkElement {
  const link = document.createElement("link");
  link.rel = "dns-prefetch";
  link.href = domain;
  document.head.appendChild(link);
  return link;
}

/**
 * 预连接（包含 DNS 解析、TCP 握手、TLS 协商）
 * @param origin 源地址
 */
export function preconnect(origin: string): HTMLLinkElement {
  const link = document.createElement("link");
  link.rel = "preconnect";
  link.href = origin;
  link.crossOrigin = "anonymous";
  document.head.appendChild(link);
  return link;
}

/**
 * 批量预加载资源
 * @param configs 预加载配置列表
 */
export function preloadResources(configs: PreloadConfig[]): HTMLLinkElement[] {
  return configs.map((config) => preloadResource(config));
}

/**
 * 空闲时预加载
 * @param callback 预加载回调
 */
export function preloadOnIdle(callback: () => void): void {
  if ("requestIdleCallback" in window) {
    requestIdleCallback(callback, { timeout: 2000 });
  } else {
    setTimeout(callback, 100);
  }
}

/**
 * 检测网络状况
 */
export function getNetworkInfo(): {
  effectiveType: string;
  downlink: number;
  rtt: number;
  saveData: boolean;
} {
  const connection =
    (navigator as any).connection ||
    (navigator as any).mozConnection ||
    (navigator as any).webkitConnection;

  return {
    effectiveType: connection?.effectiveType || "4g",
    downlink: connection?.downlink || 10,
    rtt: connection?.rtt || 50,
    saveData: connection?.saveData || false,
  };
}

/**
 * 根据网络状况决定是否预加载
 */
export function shouldPreload(): boolean {
  const { effectiveType, saveData } = getNetworkInfo();

  // 如果用户开启了省流量模式，不预加载
  if (saveData) return false;

  // 2G 网络不预加载
  if (effectiveType === "slow-2g" || effectiveType === "2g") return false;

  return true;
}

/**
 * 性能标记
 * @param name 标记名称
 */
export function performanceMark(name: string): void {
  if (performance && performance.mark) {
    performance.mark(name);
  }
}

/**
 * 性能测量
 * @param name 测量名称
 * @param startMark 开始标记
 * @param endMark 结束标记
 */
export function performanceMeasure(
  name: string,
  startMark: string,
  endMark: string,
): PerformanceMeasure | null {
  if (performance && performance.measure) {
    try {
      return performance.measure(name, startMark, endMark);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * 获取页面加载性能指标
 */
export function getPageLoadMetrics(): Record<string, number> {
  if (!performance || !performance.timing) {
    return {};
  }

  const timing = performance.timing;
  const navigationStart = timing.navigationStart;

  return {
    // DNS 查询时间
    dns: timing.domainLookupEnd - timing.domainLookupStart,
    // TCP 连接时间
    tcp: timing.connectEnd - timing.connectStart,
    // 请求响应时间
    request: timing.responseEnd - timing.requestStart,
    // DOM 解析时间
    domParse: timing.domInteractive - timing.responseEnd,
    // DOM 完成时间
    domComplete: timing.domComplete - timing.domInteractive,
    // 页面加载总时间
    loadTime: timing.loadEventEnd - navigationStart,
    // 首字节时间 (TTFB)
    ttfb: timing.responseStart - navigationStart,
    // 白屏时间
    whiteScreen: timing.domLoading - navigationStart,
    // 首次可交互时间
    interactive: timing.domInteractive - navigationStart,
  };
}

/**
 * 监控长任务
 * @param callback 回调函数
 * @param threshold 阈值（毫秒）
 */
export function observeLongTasks(
  callback: (entry: PerformanceEntry) => void,
  threshold: number = 50,
): PerformanceObserver | null {
  if (!("PerformanceObserver" in window)) {
    return null;
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.duration > threshold) {
          callback(entry);
        }
      }
    });

    observer.observe({ entryTypes: ["longtask"] });
    return observer;
  } catch {
    return null;
  }
}

/**
 * 监控资源加载
 * @param callback 回调函数
 */
export function observeResourceTiming(
  callback: (entry: PerformanceResourceTiming) => void,
): PerformanceObserver | null {
  if (!("PerformanceObserver" in window)) {
    return null;
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        callback(entry as PerformanceResourceTiming);
      }
    });

    observer.observe({ entryTypes: ["resource"] });
    return observer;
  } catch {
    return null;
  }
}

/**
 * 图片懒加载观察器
 * @param options IntersectionObserver 配置
 */
export function createImageLazyLoader(
  options: IntersectionObserverInit = {},
): IntersectionObserver | null {
  if (!("IntersectionObserver" in window)) {
    return null;
  }

  const defaultOptions: IntersectionObserverInit = {
    root: null,
    rootMargin: "50px",
    threshold: 0.1,
    ...options,
  };

  return new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        const src = img.dataset.src;

        if (src) {
          img.src = src;
          img.removeAttribute("data-src");
          observer.unobserve(img);
        }
      }
    });
  }, defaultOptions);
}

/**
 * 关键路由列表（需要优先预加载）
 */
export const CRITICAL_ROUTES = [
  "Dashboard",
  "Projects",
  "Villages",
  "Statistics",
];

/**
 * 预加载关键路由
 */
export function preloadCriticalRoutes(): void {
  if (!shouldPreload()) return;

  preloadOnIdle(() => {
    // 预加载关键视图组件
    const criticalImports = [
      () => import("@/views/HomeSafe.vue"),
      () => import("@/views/projects/List.vue"),
      () => import("@/views/analytics/supported-villages/List.vue"),
      () => import("@/views/dataAnalysis/Index.vue"),
    ];

    criticalImports.forEach((importFn) => {
      importFn().catch(() => {
        // 静默处理预加载失败
      });
    });
  });
}

/**
 * 初始化性能优化
 */
export function initPerformanceOptimizations(): void {
  // 预连接 API 服务器
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
  if (apiBaseUrl) {
    try {
      const url = new URL(apiBaseUrl);
      preconnect(url.origin);
    } catch {
      // 忽略无效 URL
    }
  }

  // 空闲时预加载关键路由
  preloadCriticalRoutes();

  // 监控长任务（开发环境，阈值 200ms 避免首屏初始化等正常任务刷屏）
  if (import.meta.env.DEV) {
    observeLongTasks((entry) => {
      logger.warn("[Performance] 检测到长任务:", {
        name: entry.name,
        duration: `${entry.duration.toFixed(2)}ms`,
        startTime: entry.startTime,
      });
    }, 200);
  }
}

export default {
  createAsyncComponent,
  preloadResource,
  prefetchResource,
  dnsPrefetch,
  preconnect,
  preloadResources,
  preloadOnIdle,
  getNetworkInfo,
  shouldPreload,
  performanceMark,
  performanceMeasure,
  getPageLoadMetrics,
  observeLongTasks,
  observeResourceTiming,
  createImageLazyLoader,
  preloadCriticalRoutes,
  initPerformanceOptimizations,
};

// ============================================================================
// Web Vitals 报告 — 首次加载性能监控
// ============================================================================

/**
 * 上报核心 Web Vitals 指标 (FCP, LCP, CLS, FID, TTFB)
 * 用于验证首屏加载优化效果
 */
export function reportWebVitals(): void {
  if (!("PerformanceObserver" in window)) return

  // FCP (First Contentful Paint)
  try {
    const fcpObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntriesByName("first-contentful-paint")) {
        const fcp = entry.startTime
        console.debug(`[WebVital] FCP: ${fcp.toFixed(0)}ms`)
        performanceMonitor.recordMetric("FCP", fcp, { unit: "ms" })
      }
    })
    fcpObserver.observe({ type: "paint", buffered: true })
  } catch { /* ignore */ }

  // LCP (Largest Contentful Paint)
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      const lastEntry = entries[entries.length - 1]
      if (lastEntry) {
        const lcp = lastEntry.startTime
        console.debug(`[WebVital] LCP: ${lcp.toFixed(0)}ms`)
        performanceMonitor.recordMetric("LCP", lcp, { unit: "ms" })
      }
    })
    lcpObserver.observe({ type: "largest-contentful-paint", buffered: true })
  } catch { /* ignore */ }

  // CLS (Cumulative Layout Shift)
  let clsValue = 0
  try {
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!(entry as any).hadRecentInput) {
          clsValue += (entry as any).value
          performanceMonitor.recordMetric("CLS", clsValue, { unit: "score" })
        }
      }
    })
    clsObserver.observe({ type: "layout-shift", buffered: true })
  } catch { /* ignore */ }

  // FID (First Input Delay) / INP (Interaction to Next Paint)
  try {
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const fid = entry.duration
        console.debug(`[WebVital] FID: ${fid.toFixed(0)}ms`)
        performanceMonitor.recordMetric("FID", fid, { unit: "ms" })
      }
    })
    fidObserver.observe({ type: "first-input", buffered: true })
  } catch { /* ignore */ }

  // TTFB (Time to First Byte) — for API calls
  try {
    const navEntries = performance.getEntriesByType("navigation") as PerformanceNavigationTiming[]
    if (navEntries.length > 0) {
      const ttfb = navEntries[0].responseStart - navEntries[0].requestStart
      performanceMonitor.recordMetric("TTFB", ttfb, { unit: "ms" })
    }
  } catch { /* ignore */ }
}

// ============================================================================
// 兼容性导出 - 保持与现有测试的兼容性
// ============================================================================

/**
 * 性能指标记录
 */
interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  tags?: Record<string, unknown>;
}

/**
 * 性能监控器
 */
class PerformanceMonitorClass {
  private metrics: Map<string, PerformanceMetric[]> = new Map();
  private maxMetrics = 1000;

  /**
   * 记录性能指标
   */
  recordMetric(
    name: string,
    value: number,
    tags?: Record<string, unknown>,
  ): void {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      tags,
    };

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }

    const metricList = this.metrics.get(name)!;
    metricList.push(metric);

    // 限制指标数量
    if (metricList.length > this.maxMetrics) {
      metricList.shift();
    }
  }

  /**
   * 获取指定名称的指标
   */
  getMetrics(name: string): PerformanceMetric[] {
    return this.metrics.get(name) || [];
  }

  /**
   * 测量同步函数执行时间
   */
  measure<T>(name: string, fn: () => T): T {
    const start = performance.now();
    let error = false;

    try {
      return fn();
    } catch (e) {
      error = true;
      throw e;
    } finally {
      const duration = performance.now() - start;
      this.recordMetric(name, duration, error ? { error: true } : undefined);
    }
  }

  /**
   * 测量异步函数执行时间
   */
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    let error = false;

    try {
      return await fn();
    } catch (e) {
      error = true;
      throw e;
    } finally {
      const duration = performance.now() - start;
      this.recordMetric(name, duration, error ? { error: true } : undefined);
    }
  }

  /**
   * 获取指标平均值
   */
  getAverage(name: string): number | null {
    const metrics = this.getMetrics(name);
    if (metrics.length === 0) return null;

    const sum = metrics.reduce((acc, m) => acc + m.value, 0);
    return sum / metrics.length;
  }

  /**
   * 生成性能报告
   */
  getReport(): Record<
    string,
    { count: number; average: string; max: string; min: string }
  > {
    const report: Record<
      string,
      { count: number; average: string; max: string; min: string }
    > = {};

    this.metrics.forEach((metrics, name) => {
      if (metrics.length === 0) return;

      const values = metrics.map((m) => m.value);
      const sum = values.reduce((a, b) => a + b, 0);
      const avg = sum / values.length;
      const max = Math.max(...values);
      const min = Math.min(...values);

      report[name] = {
        count: metrics.length,
        average: avg.toFixed(2),
        max: max.toFixed(2),
        min: min.toFixed(2),
      };
    });

    return report;
  }

  /**
   * 清除所有指标
   */
  clear(): void {
    this.metrics.clear();
  }
}

/**
 * 性能监控器单例
 */
export const performanceMonitor = new PerformanceMonitorClass();

/**
 * 防抖函数
 * @param fn 要防抖的函数
 * @param delay 延迟时间（毫秒）
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number,
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function (this: unknown, ...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn.apply(this, args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * 节流函数
 * @param fn 要节流的函数
 * @param limit 限制时间（毫秒）
 */
export function throttle<T extends (...args: unknown[]) => unknown>(
  fn: T,
  limit: number,
): (...args: Parameters<T>) => void {
  let lastCall = 0;

  return function (this: unknown, ...args: Parameters<T>) {
    const now = Date.now();

    if (now - lastCall >= limit) {
      lastCall = now;
      fn.apply(this, args);
    }
  };
}

/**
 * 记忆化函数
 * @param fn 要记忆化的函数
 * @param maxSize 最大缓存大小
 */
export function memoize<T extends (...args: unknown[]) => unknown>(
  fn: T,
  maxSize: number = 100,
): T {
  const cache = new Map<string, ReturnType<T>>();
  const keys: string[] = [];

  return function (this: unknown, ...args: Parameters<T>): ReturnType<T> {
    const key = JSON.stringify(args);

    if (cache.has(key)) {
      return cache.get(key)!;
    }

    const result = fn.apply(this, args) as ReturnType<T>;

    // 限制缓存大小
    if (keys.length >= maxSize) {
      const oldestKey = keys.shift()!;
      cache.delete(oldestKey);
    }

    cache.set(key, result);
    keys.push(key);

    return result;
  } as T;
}

/**
 * 懒加载函数
 * @param importFunc 动态导入函数
 * @param componentName 组件名称（用于性能监控）
 */
export function lazyLoad<T>(
  importFunc: () => Promise<T>,
  componentName: string,
): () => Promise<T> {
  return async () => {
    const start = performance.now();
    const result = await importFunc();
    const duration = performance.now() - start;

    performanceMonitor.recordMetric("component_load", duration, {
      component: componentName,
    });

    return result;
  };
}
