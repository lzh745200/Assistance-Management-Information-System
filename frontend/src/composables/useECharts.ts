/**
 * useECharts — 自动管理 ECharts 实例生命周期的 Composable
 *
 * 自动在组件卸载时调用 dispose()，并在窗口 resize 时触发 resize()。
 * 零内存泄漏，开箱即用。
 *
 * Usage:
 *   const { chartRef, setOption } = useECharts();
 *   // template: <div ref="chartRef" style="width:100%;height:300px"></div>
 *   setOption({ ... }); // 自动初始化 + 自动销毁
 */

import { ref, onMounted, onUnmounted, type Ref } from 'vue'
import type { EChartsOption, ECharts } from 'echarts'

interface UseEChartsOptions {
  /** 是否自动监听 window resize（默认 true） */
  autoResize?: boolean
  /** resize 防抖延迟 (ms)，默认 100 */
  resizeDebounce?: number
}

interface UseEChartsReturn {
  /** 模板 ref 绑定的 DOM 元素 */
  chartRef: Ref<HTMLElement | null>
  /** 当前 ECharts 实例（只读） */
  instance: Ref<ECharts | null>
  /** 设置/更新图表配置 */
  setOption: (option: EChartsOption, opts?: { notMerge?: boolean; lazyUpdate?: boolean }) => void
  /** 手动调整图表大小 */
  resize: () => void
  /** 获取图表 Base64 截图 */
  getDataURL: () => string
}

export function useECharts(opts: UseEChartsOptions = {}): UseEChartsReturn {
  const { autoResize = true, resizeDebounce = 100 } = opts

  const chartRef = ref<HTMLElement | null>(null)
  const instance = ref<ECharts | null>(null) as Ref<ECharts | null>

  let _resizeTimer: ReturnType<typeof setTimeout> | null = null

  function _onResize() {
    if (_resizeTimer) clearTimeout(_resizeTimer)
    _resizeTimer = setTimeout(() => {
      instance.value?.resize()
    }, resizeDebounce)
  }

  async function _init() {
    if (!chartRef.value) return
    // 动态导入 echarts（支持 code-splitting）
    const echarts = await import('echarts')
    instance.value = echarts.init(chartRef.value)
    if (autoResize) {
      window.addEventListener('resize', _onResize)
    }
  }

  function setOption(
    option: EChartsOption,
    setOpts?: { notMerge?: boolean; lazyUpdate?: boolean }
  ) {
    if (!instance.value) return
    instance.value.setOption(option, setOpts)
  }

  function resize() {
    instance.value?.resize()
  }

  function getDataURL(): string {
    return instance.value?.getDataURL() ?? ''
  }

  onMounted(async () => {
    await _init()
  })

  onUnmounted(() => {
    if (_resizeTimer) clearTimeout(_resizeTimer)
    if (autoResize) {
      window.removeEventListener('resize', _onResize)
    }
    instance.value?.dispose()
    instance.value = null
  })

  return { chartRef, instance, setOption, resize, getDataURL }
}
