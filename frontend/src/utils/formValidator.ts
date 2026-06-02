/**
 * 表单校验工具
 *
 * 实现防抖校验逻辑，减少校验频率
 *
 * _需求: 5.4_
 */

import { createDebounce } from "@/composables/useDebounce";

// ==================== 类型定义 ====================

/** 校验规则 */
export interface ValidationRule {
  /** 是否必填 */
  required?: boolean;
  /** 必填提示消息 */
  message?: string;
  /** 最小长度 */
  min?: number;
  /** 最大长度 */
  max?: number;
  /** 正则表达式 */
  pattern?: RegExp;
  /** 自定义校验函数 */
  validator?: (value: any) => boolean | string | Promise<boolean | string>;
  /** 触发方式 */
  trigger?: "blur" | "change" | "submit";
}

/** 校验结果 */
export interface ValidationResult {
  /** 是否有效 */
  valid: boolean;
  /** 错误消息 */
  message: string;
}

/** 字段校验状态 */
export interface FieldValidationState {
  /** 是否正在校验 */
  validating: boolean;
  /** 是否有效 */
  valid: boolean;
  /** 错误消息 */
  message: string;
  /** 是否已触发过校验 */
  touched: boolean;
}

/** 表单校验器配置 */
export interface FormValidatorOptions {
  /** 防抖延迟时间（毫秒） */
  debounceDelay?: number;
  /** 是否在首次输入时立即校验 */
  validateOnMount?: boolean;
}

// ==================== 默认配置 ====================

const DEFAULT_DEBOUNCE_DELAY = 300;

// ==================== 校验函数 ====================

/**
 * 校验单个值
 * @param value 要校验的值
 * @param rules 校验规则
 * @returns 校验结果
 */
export async function validateValue(
  value: any,
  rules: ValidationRule[],
): Promise<ValidationResult> {
  for (const rule of rules) {
    // 必填校验
    if (rule.required) {
      const isEmpty =
        value === undefined ||
        value === null ||
        value === "" ||
        (Array.isArray(value) && value.length === 0);

      if (isEmpty) {
        return {
          valid: false,
          message: rule.message || "此字段为必填项",
        };
      }
    }

    // 如果值为空且非必填，跳过后续校验
    if (value === undefined || value === null || value === "") {
      continue;
    }

    // 最小长度校验
    if (rule.min !== undefined) {
      const length =
        typeof value === "string"
          ? value.length
          : Array.isArray(value)
            ? value.length
            : 0;

      if (length < rule.min) {
        return {
          valid: false,
          message: rule.message || `长度不能少于 ${rule.min} 个字符`,
        };
      }
    }

    // 最大长度校验
    if (rule.max !== undefined) {
      const length =
        typeof value === "string"
          ? value.length
          : Array.isArray(value)
            ? value.length
            : 0;

      if (length > rule.max) {
        return {
          valid: false,
          message: rule.message || `长度不能超过 ${rule.max} 个字符`,
        };
      }
    }

    // 正则校验
    if (rule.pattern) {
      if (!rule.pattern.test(String(value))) {
        return {
          valid: false,
          message: rule.message || "格式不正确",
        };
      }
    }

    // 自定义校验
    if (rule.validator) {
      try {
        const result = await rule.validator(value);

        if (result === false) {
          return {
            valid: false,
            message: rule.message || "校验失败",
          };
        }

        if (typeof result === "string") {
          return {
            valid: false,
            message: result,
          };
        }
      } catch (error) {
        return {
          valid: false,
          message: rule.message || "校验出错",
        };
      }
    }
  }

  return {
    valid: true,
    message: "",
  };
}

// ==================== 表单校验器类 ====================

/**
 * 表单校验器
 *
 * 提供防抖校验功能
 *
 * @example
 * ```ts
 * const validator = new FormValidator({
 *   debounceDelay: 300
 * })
 *
 * // 添加字段规则
 * validator.addField('username', [
 *   { required: true, message: '请输入用户名' },
 *   { min: 3, max: 20, message: '用户名长度为3-20个字符' }
 * ])
 *
 * // 校验字段
 * const result = await validator.validateField('username', 'test')
 *
 * // 校验所有字段
 * const allResults = await validator.validateAll({
 *   username: 'test',
 *   password: '123456'
 * })
 * ```
 */
export class FormValidator {
  private rules: Map<string, ValidationRule[]> = new Map();
  private states: Map<string, FieldValidationState> = new Map();
  private debouncedValidators: Map<string, ReturnType<typeof createDebounce>> =
    new Map();
  private debounceDelay: number;
  private validateCallCount: number = 0;

  constructor(options: FormValidatorOptions = {}) {
    this.debounceDelay = options.debounceDelay ?? DEFAULT_DEBOUNCE_DELAY;
  }

  /**
   * 添加字段规则
   * @param field 字段名
   * @param rules 校验规则
   */
  addField(field: string, rules: ValidationRule[]): void {
    this.rules.set(field, rules);
    this.states.set(field, {
      validating: false,
      valid: true,
      message: "",
      touched: false,
    });
  }

  /**
   * 移除字段规则
   * @param field 字段名
   */
  removeField(field: string): void {
    this.rules.delete(field);
    this.states.delete(field);

    const debounced = this.debouncedValidators.get(field);
    if (debounced) {
      debounced.cancel();
      this.debouncedValidators.delete(field);
    }
  }

  /**
   * 获取字段状态
   * @param field 字段名
   */
  getFieldState(field: string): FieldValidationState | undefined {
    return this.states.get(field);
  }

  /**
   * 获取所有字段状态
   */
  getAllStates(): Map<string, FieldValidationState> {
    return new Map(this.states);
  }

  /**
   * 校验字段（立即执行）
   * @param field 字段名
   * @param value 字段值
   */
  async validateField(field: string, value: any): Promise<ValidationResult> {
    const rules = this.rules.get(field);
    if (!rules) {
      return { valid: true, message: "" };
    }

    const state = this.states.get(field);
    if (state) {
      state.validating = true;
      state.touched = true;
    }

    this.validateCallCount++;
    const result = await validateValue(value, rules);

    if (state) {
      state.validating = false;
      state.valid = result.valid;
      state.message = result.message;
    }

    return result;
  }

  /**
   * 防抖校验字段
   * @param field 字段名
   * @param value 字段值
   * @param callback 校验完成回调
   */
  validateFieldDebounced(
    field: string,
    value: any,
    callback?: (result: ValidationResult) => void,
  ): void {
    let debounced = this.debouncedValidators.get(field);

    if (!debounced) {
      debounced = createDebounce(
        async (val: any, cb?: (result: ValidationResult) => void) => {
          const result = await this.validateField(field, val);
          cb?.(result);
        },
        this.debounceDelay,
      );
      this.debouncedValidators.set(field, debounced);
    }

    const state = this.states.get(field);
    if (state) {
      state.touched = true;
    }

    debounced.debouncedFn(value, callback);
  }

  /**
   * 校验所有字段
   * @param values 字段值映射
   */
  async validateAll(values: Record<string, any>): Promise<{
    valid: boolean;
    errors: Record<string, string>;
  }> {
    const errors: Record<string, string> = {};
    let valid = true;

    for (const [field] of this.rules) {
      const value = values[field];
      const result = await this.validateField(field, value);

      if (!result.valid) {
        valid = false;
        errors[field] = result.message;
      }
    }

    return { valid, errors };
  }

  /**
   * 重置字段状态
   * @param field 字段名（可选，不传则重置所有）
   */
  reset(field?: string): void {
    if (field) {
      const state = this.states.get(field);
      if (state) {
        state.validating = false;
        state.valid = true;
        state.message = "";
        state.touched = false;
      }

      const debounced = this.debouncedValidators.get(field);
      if (debounced) {
        debounced.cancel();
      }
    } else {
      for (const [, state] of this.states) {
        state.validating = false;
        state.valid = true;
        state.message = "";
        state.touched = false;
      }

      for (const debounced of this.debouncedValidators.values()) {
        debounced.cancel();
      }
    }
  }

  /**
   * 获取校验调用次数（用于测试）
   */
  getValidateCallCount(): number {
    return this.validateCallCount;
  }

  /**
   * 重置校验调用次数（用于测试）
   */
  resetValidateCallCount(): void {
    this.validateCallCount = 0;
  }

  /**
   * 销毁校验器
   */
  destroy(): void {
    for (const debounced of this.debouncedValidators.values()) {
      debounced.cancel();
    }
    this.debouncedValidators.clear();
    this.rules.clear();
    this.states.clear();
  }
}

// ==================== 便捷函数 ====================

/**
 * 创建表单校验器
 * @param options 配置选项
 */
export function createFormValidator(
  options?: FormValidatorOptions,
): FormValidator {
  return new FormValidator(options);
}

// ==================== 常用校验规则 ====================

/** 邮箱校验规则 */
export const emailRule: ValidationRule = {
  pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  message: "请输入有效的邮箱地址",
};

/** 手机号校验规则 */
export const phoneRule: ValidationRule = {
  pattern: /^1[3-9]\d{9}$/,
  message: "请输入有效的手机号码",
};

/** 身份证号校验规则 */
export const idCardRule: ValidationRule = {
  pattern:
    /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/,
  message: "请输入有效的身份证号码",
};

/** URL校验规则 */
export const urlRule: ValidationRule = {
  pattern: /^https?:\/\/.+/,
  message: "请输入有效的URL地址",
};

/** 必填规则 */
export const requiredRule = (message?: string): ValidationRule => ({
  required: true,
  message: message || "此字段为必填项",
});

/** 长度范围规则 */
export const lengthRule = (
  min: number,
  max: number,
  message?: string,
): ValidationRule => ({
  min,
  max,
  message: message || `长度应在 ${min} 到 ${max} 个字符之间`,
});

export default FormValidator;
