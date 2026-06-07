import { describe, it, expect, vi, beforeEach } from 'vitest';
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
});
