import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('element-plus', () => ({
  ElMessage: { warning: vi.fn() },
}));

import { ElMessage } from 'element-plus';
import { checkVersion } from '@/composables/useVersionCheck';

describe('useVersionCheck/checkVersion', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('version matches → does not reload', async () => {
    localStorage.setItem('app_version', '1.3.0');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ version: '1.3.0' }),
    });
    const reloadSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: reloadSpy },
      writable: true,
    });
    await checkVersion();
    expect(reloadSpy).not.toHaveBeenCalled();
  });

  it('version mismatch → does not throw', async () => {
    localStorage.setItem('app_version', '1.2.0');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ version: '1.3.0' }),
    });
    // checkVersion schedules reload via setTimeout — test it doesn't throw
    await expect(checkVersion()).resolves.toBeUndefined();
  });

  it('fetch failure (404) → silent skip, no exception', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('network error'));
    await expect(checkVersion()).resolves.toBeUndefined();
  });

  it('first visit (no cached version) → saves version, no reload', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ version: '1.3.0' }),
    });
    await checkVersion();
    expect(localStorage.getItem('app_version')).toBe('1.3.0');
  });

  it('HTTP error (ok=false) → silent skip, no write', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 });
    await expect(checkVersion()).resolves.toBeUndefined();
    expect(localStorage.getItem('app_version')).toBeNull();
  });

  it('missing version field → silent skip', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ foo: 'bar' }),
    });
    await expect(checkVersion()).resolves.toBeUndefined();
    expect(localStorage.getItem('app_version')).toBeNull();
  });

  it('version mismatch → warns and reloads after delay', async () => {
    vi.useFakeTimers();
    try {
      localStorage.setItem('app_version', '1.2.0');
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ version: '1.3.0' }),
      });
      const reload = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload },
        writable: true,
      });
      await checkVersion();
      expect(localStorage.getItem('app_version')).toBe('1.3.0');
      expect(ElMessage.warning).toHaveBeenCalledWith(
        expect.objectContaining({ message: '系统已更新至 v1.3.0，即将自动刷新...' })
      );
      expect(reload).not.toHaveBeenCalled();
      await vi.advanceTimersByTimeAsync(1500);
      expect(reload).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });
});
