/**
 * 前端性能诊断工具
 *
 * 提供 FPS 监控、内存泄漏检测、组件渲染耗时分析。
 * 仅在开发模式 (import.meta.env.DEV) 下激活。
 *
 * Usage:
 *   import { startPerfMonitor } from '@/utils/performanceDiagnostics';
 *   // 在 main.ts 中调用
 *   startPerfMonitor({ logFps: true, logMemory: true, slowComponentMs: 100 });
 */

// ── FPS 监控 ──

let _fpsFrames = 0
let _fpsLastTime = performance.now()
let _fpsValue = 60
let _fpsRafId = 0

export function startFpsMonitor(onUpdate?: (fps: number) => void): () => void {
  function _tick() {
    _fpsFrames++
    const now = performance.now()
    const elapsed = now - _fpsLastTime
    if (elapsed >= 1000) {
      _fpsValue = Math.round((_fpsFrames * 1000) / elapsed)
      _fpsFrames = 0
      _fpsLastTime = now
      onUpdate?.(_fpsValue)
      // 低帧率警告
      if (_fpsValue < 30 && import.meta.env.DEV) {
        console.warn(`[Perf] 低帧率: ${_fpsValue} FPS`)
      }
    }
    _fpsRafId = requestAnimationFrame(_tick)
  }
  _fpsRafId = requestAnimationFrame(_tick)
  return () => cancelAnimationFrame(_fpsRafId)
}

export function getCurrentFps(): number {
  return _fpsValue
}

// ── 内存监控 ──

interface MemoryInfo {
  jsHeapSizeLimit: number
  totalJSHeapSize: number
  usedJSHeapSize: number
}

export function getMemoryInfo(): MemoryInfo | null {
  const perf = performance as any
  if (perf?.memory) {
    return {
      jsHeapSizeLimit: perf.memory.jsHeapSizeLimit,
      totalJSHeapSize: perf.memory.totalJSHeapSize,
      usedJSHeapSize: perf.memory.usedJSHeapSize,
    }
  }
  return null
}

let _memIntervalId = 0

export function startMemoryMonitor(
  intervalMs: number = 10000,
  onLeak?: (growthMb: number) => void
): () => void {
  let lastUsed = 0
  _memIntervalId = window.setInterval(() => {
    const mem = getMemoryInfo()
    if (!mem) return
    const usedMb = mem.usedJSHeapSize / 1024 / 1024
    if (lastUsed > 0) {
      const growth = usedMb - lastUsed
      if (growth > 10) {
        console.warn(
          `[Perf] 内存增长 ${growth.toFixed(1)}MB (当前 ${usedMb.toFixed(1)}MB)` +
            ` — 可能存在内存泄漏`
        )
        onLeak?.(growth)
      }
    }
    lastUsed = usedMb
  }, intervalMs)
  return () => clearInterval(_memIntervalId)
}

// ── 组件渲染耗时 ──

const _renderTimes = new Map<string, number[]>()

export function recordRender(componentName: string): () => void {
  const start = performance.now()
  return () => {
    const elapsed = performance.now() - start
    if (!_renderTimes.has(componentName)) {
      _renderTimes.set(componentName, [])
    }
    _renderTimes.get(componentName)!.push(elapsed)
  }
}

export function getRenderStats(componentName: string) {
  const times = _renderTimes.get(componentName) || []
  if (!times.length) return null
  const sum = times.reduce((a, b) => a + b, 0)
  return {
    count: times.length,
    avg_ms: Math.round(sum / times.length),
    max_ms: Math.round(Math.max(...times)),
    min_ms: Math.round(Math.min(...times)),
  }
}

// ── 统一启动入口 ──

interface PerfMonitorOptions {
  logFps?: boolean
  logMemory?: boolean
  slowComponentMs?: number
}

let _cleanups: (() => void)[] = []

export function startPerfMonitor(opts: PerfMonitorOptions = {}): () => void {
  if (!import.meta.env.DEV) return () => {}

  _cleanups.forEach((fn) => fn())
  _cleanups = []

  if (opts.logFps) {
    _cleanups.push(
      startFpsMonitor((fps) => {
        if (fps < 30) console.debug(`[Perf] FPS: ${fps}`)
      })
    )
  }

  if (opts.logMemory) {
    _cleanups.push(startMemoryMonitor(15000))
  }

  console.log('[Perf] 性能监控已启动', opts)
  return () => _cleanups.forEach((fn) => fn())
}
