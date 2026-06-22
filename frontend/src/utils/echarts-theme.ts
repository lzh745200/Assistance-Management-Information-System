/**
 * ECharts "军队科技风" 主题配置
 *
 * 设计理念：
 * - 军队蓝 (#1e4d8c) + 振兴绿 (#2d6a4f) + 点缀金 (#b8960c) 为品牌色系
 * - 低饱和度配色，去除冗余视觉噪音
 * - 干净克制的坐标轴、网格线、Tooltip
 * - 与 dashboard-theme.scss 中的 CSS 变量保持一致
 *
 * 使用方式：
 *   import { registerMilitaryTheme } from "@/utils/echarts-theme";
 *   registerMilitaryTheme(); // 在应用初始化时调用一次
 *   // 之后 echarts.init(dom, "militaryTech") 即可使用
 */

import type { EChartsCoreOption } from 'echarts/core'
import echarts from '@/utils/echarts'

// ============================================================================
// 色彩体系
// ============================================================================

/** 品牌色板 —— 16 色，覆盖饼图/柱图等多系列场景 */
const COLOR_PALETTE = [
  '#1e4d8c', // 军队蓝（主）
  '#2d6a4f', // 振兴绿
  '#b8960c', // 点缀金
  '#3b82f6', // 亮蓝
  '#52b788', // 亮绿
  '#f59e0b', // 琥珀
  '#ef4444', // 警示红
  '#8b5cf6', // 紫罗兰
  '#06b6d4', // 青色
  '#84cc16', // 柠檬绿
  '#f97316', // 橙色
  '#ec4899', // 粉红
  '#6366f1', // 靛蓝
  '#14b8a6', // 薄荷
  '#e11d48', // 玫红
  '#64748b', // 石板灰
]

// ============================================================================
// 主题配置
// ============================================================================

interface ThemeConfig {
  color: string[]
  backgroundColor: string
  textStyle: {
    color: string
    fontFamily: string
  }
  title: {
    textStyle: { color: string; fontWeight: number | string; fontSize: number }
    subtextStyle: { color: string; fontSize: number }
  }
  line: {
    itemStyle: { borderWidth: number }
    lineStyle: { width: number }
    symbolSize: number
    symbol: string
    smooth: boolean
  }
  bar: {
    itemStyle: {
      barBorderWidth: number
      barBorderColor: string
      borderRadius: number[]
    }
    emphasis: {
      itemStyle: {
        barBorderWidth: number
        barBorderColor: string
      }
    }
  }
  pie: {
    itemStyle: {
      borderWidth: number
      borderColor: string
      borderRadius: number
    }
    emphasis: {
      itemStyle: {
        shadowBlur: number
        shadowOffsetX: number
        shadowColor: string
      }
    }
  }
  categoryAxis: {
    axisLine: {
      show: boolean
      lineStyle: { color: string }
    }
    axisTick: { show: boolean }
    axisLabel: { color: string; fontSize: number }
    splitLine: { show: boolean }
    nameTextStyle: { color: string; fontSize: number }
  }
  valueAxis: {
    axisLine: { show: boolean }
    axisTick: { show: boolean }
    axisLabel: { color: string; fontSize: number }
    splitLine: {
      show: boolean
      lineStyle: { color: string; type: string; width: number }
    }
    nameTextStyle: { color: string; fontSize: number }
  }
  logAxis: {
    axisLine: { show: boolean }
    axisTick: { show: boolean }
    axisLabel: { color: string; fontSize: number }
    splitLine: {
      show: boolean
      lineStyle: { color: string; type: string; width: number }
    }
  }
  timeAxis: {
    axisLine: { show: boolean; lineStyle: { color: string } }
    axisTick: { show: boolean }
    axisLabel: { color: string; fontSize: number }
    splitLine: { show: boolean }
  }
  toolbox: {
    iconStyle: {
      borderColor: string
    }
    emphasis: {
      iconStyle: {
        borderColor: string
      }
    }
  }
  legend: {
    textStyle: { color: string; fontSize: number }
  }
  tooltip: {
    axisPointer: {
      lineStyle: { color: string; width: number }
      crossStyle: { color: string; width: number }
    }
  }
  dataZoom: {
    dataBackground: {
      lineStyle: { color: string }
      areaStyle: { color: string }
    }
    selectedDataBackground: {
      lineStyle: { color: string }
      areaStyle: { color: string }
    }
    handleStyle: { color: string }
    textStyle: { color: string }
  }
}

// ============================================================================
// 浅色主题 —— 干净、克制、科技感
// ============================================================================

const militaryTechTheme: ThemeConfig = {
  color: COLOR_PALETTE,

  backgroundColor: 'transparent',

  textStyle: {
    color: '#1e293b',
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Microsoft YaHei', 'PingFang SC', sans-serif",
  },

  // ── 标题 ──
  title: {
    textStyle: {
      color: '#0f172a',
      fontWeight: 600,
      fontSize: 16,
    },
    subtextStyle: {
      color: '#94a3b8',
      fontSize: 12,
    },
  },

  // ── 折线图 ──
  line: {
    itemStyle: {
      borderWidth: 2,
    },
    lineStyle: {
      width: 3,
    },
    symbolSize: 6,
    symbol: 'circle',
    smooth: false,
  },

  // ── 柱状图 ──
  bar: {
    itemStyle: {
      barBorderWidth: 0,
      barBorderColor: 'transparent',
      borderRadius: [6, 6, 0, 0],
    },
    emphasis: {
      itemStyle: {
        barBorderWidth: 0,
        barBorderColor: 'transparent',
      },
    },
  },

  // ── 饼图 ──
  pie: {
    itemStyle: {
      borderWidth: 3,
      borderColor: '#ffffff',
      borderRadius: 4,
    },
    emphasis: {
      itemStyle: {
        shadowBlur: 20,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.12)',
      },
    },
  },

  // ── 类目轴（X 轴） ──
  categoryAxis: {
    axisLine: {
      show: true,
      lineStyle: { color: '#e2e8f0' },
    },
    axisTick: { show: false },
    axisLabel: {
      color: '#94a3b8',
      fontSize: 11,
    },
    splitLine: { show: false },
    nameTextStyle: {
      color: '#94a3b8',
      fontSize: 11,
    },
  },

  // ── 数值轴（Y 轴） ──
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: {
      color: '#94a3b8',
      fontSize: 11,
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: '#f1f5f9',
        type: 'dashed',
        width: 1,
      },
    },
    nameTextStyle: {
      color: '#94a3b8',
      fontSize: 11,
    },
  },

  // ── 对数轴 ──
  logAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: {
      color: '#94a3b8',
      fontSize: 11,
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: '#f1f5f9',
        type: 'dashed',
        width: 1,
      },
    },
  },

  // ── 时间轴 ──
  timeAxis: {
    axisLine: {
      show: true,
      lineStyle: { color: '#e2e8f0' },
    },
    axisTick: { show: false },
    axisLabel: {
      color: '#94a3b8',
      fontSize: 11,
    },
    splitLine: { show: false },
  },

  // ── 工具箱 ──
  toolbox: {
    iconStyle: {
      borderColor: '#94a3b8',
    },
    emphasis: {
      iconStyle: {
        borderColor: '#1e4d8c',
      },
    },
  },

  // ── 图例 ──
  legend: {
    textStyle: {
      color: '#64748b',
      fontSize: 12,
    },
  },

  // ── 提示框辅助线 ──
  tooltip: {
    axisPointer: {
      lineStyle: {
        color: '#94a3b8',
        width: 1,
      },
      crossStyle: {
        color: '#94a3b8',
        width: 1,
      },
    },
  },

  // ── 数据缩放 ──
  dataZoom: {
    dataBackground: {
      lineStyle: { color: '#cbd5e1' },
      areaStyle: { color: 'rgba(203, 213, 225, 0.15)' },
    },
    selectedDataBackground: {
      lineStyle: { color: '#1e4d8c' },
      areaStyle: { color: 'rgba(30, 77, 140, 0.1)' },
    },
    handleStyle: { color: '#94a3b8' },
    textStyle: { color: '#94a3b8' },
  },
}

// ============================================================================
// 暗色主题变体 —— 兼容 [data-theme="dark"]
// ============================================================================

const militaryTechDarkTheme: ThemeConfig = {
  ...militaryTechTheme,

  backgroundColor: 'transparent',

  textStyle: {
    ...militaryTechTheme.textStyle,
    color: '#e2e8f0',
  },

  title: {
    textStyle: {
      color: '#f1f5f9',
      fontWeight: 600,
      fontSize: 16,
    },
    subtextStyle: {
      color: '#64748b',
      fontSize: 12,
    },
  },

  categoryAxis: {
    ...militaryTechTheme.categoryAxis,
    axisLine: {
      show: true,
      lineStyle: { color: '#334155' },
    },
    axisLabel: {
      color: '#64748b',
      fontSize: 11,
    },
  },

  valueAxis: {
    ...militaryTechTheme.valueAxis,
    axisLabel: {
      color: '#64748b',
      fontSize: 11,
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'rgba(51, 65, 85, 0.5)',
        type: 'dashed',
        width: 1,
      },
    },
  },

  legend: {
    textStyle: {
      color: '#94a3b8',
      fontSize: 12,
    },
  },

  tooltip: {
    axisPointer: {
      lineStyle: {
        color: '#475569',
        width: 1,
      },
      crossStyle: {
        color: '#475569',
        width: 1,
      },
    },
  },
}

// ============================================================================
// 主题注册
// ============================================================================

let isThemeRegistered = false

/**
 * 注册 ECharts 军队科技风主题。
 * 幂等调用——多次调用仅首次生效。
 *
 * 注册后可通过以下方式使用：
 * - `echarts.init(dom, "militaryTech")`     → 浅色主题
 * - `echarts.init(dom, "militaryTechDark")` → 暗色主题
 */
export function registerMilitaryTheme(): void {
  if (isThemeRegistered) return

  echarts.registerTheme('militaryTech', militaryTechTheme as unknown as EChartsCoreOption)
  echarts.registerTheme('militaryTechDark', militaryTechDarkTheme as unknown as EChartsCoreOption)

  isThemeRegistered = true
}

/**
 * 根据当前 DOM 环境自动选择主题。
 * 检测 document.documentElement 的 data-theme 属性：
 * - `data-theme="dark"` → "militaryTechDark"
 * - 其他 → "militaryTech"（默认浅色）
 */
export function getCurrentTheme(): string {
  if (typeof document !== 'undefined') {
    const theme = document.documentElement.getAttribute('data-theme')
    if (theme === 'dark') return 'militaryTechDark'
  }
  return 'militaryTech'
}

// ============================================================================
// 导出色彩常量（供外部直接引用，无需走 registerTheme）
// ============================================================================

export { COLOR_PALETTE }
export const MILITARY_BLUE = '#1e4d8c'
export const REVITALIZATION_GREEN = '#2d6a4f'
export const BADGE_GOLD = '#b8960c'
