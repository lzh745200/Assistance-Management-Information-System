/**
 * 防抖 Composable
 */
export function createDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay = 300,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
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