/**
 * 防抖 Composable
 */
export interface DebouncedFunction<T extends (...args: any[]) => any> {
  (...args: Parameters<T>): void;
  /** 取消防抖，清除待执行的定时器 */
  cancel: () => void;
  /** 立即执行（跳过防抖延迟） */
  flush: (...args: Parameters<T>) => void;
}

export function createDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay = 300,
): DebouncedFunction<T> {
  let timer: ReturnType<typeof setTimeout> | null = null;

  const debouncedFn: DebouncedFunction<T> = Object.assign(
    (...args: Parameters<T>) => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    },
    {
      cancel: () => {
        if (timer) clearTimeout(timer);
        timer = null;
      },
      flush: (...args: Parameters<T>) => {
        if (timer) clearTimeout(timer);
        timer = null;
        fn(...args);
      },
    },
  );

  return debouncedFn;
}

export function useDebounce(delayMs = 300) {
  let timer: ReturnType<typeof setTimeout> | null = null;

  function debounce(fn: () => void) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(fn, delayMs);
  }

  function cancel() {
    if (timer) clearTimeout(timer);
    timer = null;
  }

  return { debounce, cancel };
}
