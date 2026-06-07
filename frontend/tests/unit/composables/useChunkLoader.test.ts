import { describe, it, expect, vi } from 'vitest';
import { retryImport } from '@/composables/useChunkLoader';

describe('useChunkLoader/retryImport', () => {
  it('first success → returns result', async () => {
    const result = await retryImport(() => Promise.resolve('ok'), 3, 10);
    expect(result).toBe('ok');
  });

  it('1st fail, 2nd success → returns result', async () => {
    let calls = 0;
    const fn = () => {
      calls++;
      if (calls < 2) return Promise.reject(new Error('fail'));
      return Promise.resolve('retry-ok');
    };
    const result = await retryImport(fn, 3, 10);
    expect(result).toBe('retry-ok');
    expect(calls).toBe(2);
  });

  it('all failures → throws last error', async () => {
    const fn = () => Promise.reject(new Error('always-fail'));
    await expect(retryImport(fn, 3, 10)).rejects.toThrow('always-fail');
  });

  it('maxRetries=0 → no retry, throws immediately', async () => {
    const fn = () => Promise.reject(new Error('no-retry'));
    await expect(retryImport(fn, 0, 10)).rejects.toThrow('no-retry');
  });

  it('exponential backoff delay is correct', async () => {
    vi.useFakeTimers();
    let calls = 0;
    const fn = () => {
      calls++;
      return Promise.reject(new Error('fail'));
    };
    const promise = retryImport(fn, 3, 100);
    // Suppress unhandled rejection during fake timer advancement
    promise.catch(() => {});
    // 1st call fires immediately
    await vi.advanceTimersByTimeAsync(0);
    expect(calls).toBe(1);
    // 1st retry after 100ms
    await vi.advanceTimersByTimeAsync(100);
    expect(calls).toBe(2);
    // 2nd retry after 200ms
    await vi.advanceTimersByTimeAsync(200);
    expect(calls).toBe(3);
    // 3rd retry after 300ms
    await vi.advanceTimersByTimeAsync(300);
    expect(calls).toBe(4);
    vi.useRealTimers();
  });
});
