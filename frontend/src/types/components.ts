/**
 * 组件 Props 类型定义
 *
 * 定义通用组件的 Props 类型
 */

// ============================================================================
// 表格组件类型
// ============================================================================

/**
 * 表格列配置
 */
export interface TableColumn<T = unknown> {
  /** 列标识 */
  prop: keyof T | string
  /** 列标题 */
  label: string
  /** 列宽度 */
  width?: number | string
  /** 最小宽度 */
  minWidth?: number | string
  /** 是否可排序 */
  sortable?: boolean | 'custom'
  /** 对齐方式 */
  align?: 'left' | 'center' | 'right'
  /** 是否固定 */
  fixed?: boolean | 'left' | 'right'
  /** 是否显示 */
  visible?: boolean
  /** 自定义插槽名 */
  slot?: string
  /** 格式化函数 */
  formatter?: (row: T, column: TableColumn<T>, cellValue: unknown, index: number) => string
}

/**
 * 表格 Props
 */
export interface TableProps<T = unknown> {
  /** 表格数据 */
  data: T[]
  /** 列配置 */
  columns: TableColumn<T>[]
  /** 是否加载中 */
  loading?: boolean
  /** 是否显示序号 */
  showIndex?: boolean
  /** 是否显示选择框 */
  showSelection?: boolean
  /** 行唯一标识 */
  rowKey?: string | ((row: T) => string)
  /** 表格高度 */
  height?: number | string
  /** 最大高度 */
  maxHeight?: number | string
  /** 是否带边框 */
  border?: boolean
  /** 是否斜纹 */
  stripe?: boolean
  /** 空数据提示 */
  emptyText?: string
}

// ============================================================================
// 分页组件类型
// ============================================================================

/**
 * 分页 Props
 */
export interface PaginationProps {
  /** 当前页 */
  currentPage: number
  /** 每页条数 */
  pageSize: number
  /** 总条数 */
  total: number
  /** 每页条数选项 */
  pageSizes?: number[]
  /** 布局 */
  layout?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 小型分页 */
  small?: boolean
  /** 背景色 */
  background?: boolean
}

// ============================================================================
// 表单组件类型
// ============================================================================

/**
 * 表单项配置
 */
export interface FormItem {
  /** 字段名 */
  prop: string
  /** 标签 */
  label: string
  /** 类型 */
  type:
    | 'input'
    | 'select'
    | 'date'
    | 'datetime'
    | 'textarea'
    | 'number'
    | 'switch'
    | 'radio'
    | 'checkbox'
    | 'upload'
    | 'custom'
  /** 占位符 */
  placeholder?: string
  /** 是否必填 */
  required?: boolean
  /** 是否禁用 */
  disabled?: boolean
  /** 校验规则 */
  rules?: unknown[]
  /** 选项（用于 select/radio/checkbox） */
  options?: Array<{ label: string; value: unknown; disabled?: boolean }>
  /** 自定义插槽名 */
  slot?: string
  /** 栅格占位 */
  span?: number
  /** 默认值 */
  defaultValue?: unknown
}

/**
 * 表单 Props
 */
export interface FormProps {
  /** 表单数据 */
  model: Record<string, unknown>
  /** 表单项配置 */
  items: FormItem[]
  /** 标签宽度 */
  labelWidth?: string | number
  /** 标签位置 */
  labelPosition?: 'left' | 'right' | 'top'
  /** 是否禁用 */
  disabled?: boolean
  /** 列数 */
  columns?: number
  /** 是否内联 */
  inline?: boolean
}

// ============================================================================
// 对话框组件类型
// ============================================================================

/**
 * 对话框 Props
 */
export interface DialogProps {
  /** 是否显示 */
  visible: boolean
  /** 标题 */
  title?: string
  /** 宽度 */
  width?: string | number
  /** 是否全屏 */
  fullscreen?: boolean
  /** 是否显示关闭按钮 */
  showClose?: boolean
  /** 是否可以通过点击遮罩关闭 */
  closeOnClickModal?: boolean
  /** 是否可以通过按下 ESC 关闭 */
  closeOnPressEscape?: boolean
  /** 是否居中 */
  center?: boolean
  /** 是否拖拽 */
  draggable?: boolean
}

// ============================================================================
// 图表组件类型
// ============================================================================

/**
 * 图表 Props
 */
export interface ChartProps {
  /** 图表配置 */
  option: Record<string, unknown>
  /** 宽度 */
  width?: string | number
  /** 高度 */
  height?: string | number
  /** 是否加载中 */
  loading?: boolean
  /** 是否自动调整大小 */
  autoresize?: boolean
  /** 主题 */
  theme?: string | Record<string, unknown>
}

// ============================================================================
// 卡片组件类型
// ============================================================================

/**
 * 卡片 Props
 */
export interface CardProps {
  /** 标题 */
  title?: string
  /** 是否显示边框 */
  bordered?: boolean
  /** 是否悬浮时显示阴影 */
  hoverable?: boolean
  /** 是否加载中 */
  loading?: boolean
  /** 内边距 */
  bodyStyle?: Record<string, string>
}

// ============================================================================
// 通用组件类型
// ============================================================================

/**
 * 按钮类型
 */
export type ButtonType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'text' | 'default'

/**
 * 尺寸类型
 */
export type SizeType = 'large' | 'default' | 'small'

/**
 * 状态类型
 */
export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'processing' | 'default'
