import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  decodeJwtPayload,
  getTokenExpiry,
  getTimeUntilExpiry,
  isTokenExpired,
  calculateRefreshDelay,
  MAX_TIMEOUT_MS,
  DEFAULT_REFRESH_BEFORE_EXPIRY_MS,
  RECHECK_INTERVAL_MS,
  IMMEDIATE_REFRESH_THRESHOLD_MS,
} from '@/utils/jwt'

function b64url(obj: any): string {
  const json = JSON.stringify(obj)
  const b64 = btoa(unescape(encodeURIComponent(json)))
  return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

let testCounter = 0
function makeToken(payload: any, header?: any): string {
  if (!header) {
    testCounter++
    header = { alg: `T${testCounter}-${Math.random().toString(36).slice(2, 8)}` }
  }
  return `${b64url(header)}.${b64url(payload)}.sig-${Math.random().toString(36).slice(2, 10)}`
}

describe('utils/jwt', () => {
  describe('constants', () => {
    it('MAX_TIMEOUT_MS = 2^31-1', () => {
      expect(MAX_TIMEOUT_MS).toBe(2147483647)
    })
    it('DEFAULT_REFRESH_BEFORE_EXPIRY_MS = 10 min', () => {
      expect(DEFAULT_REFRESH_BEFORE_EXPIRY_MS).toBe(600000)
    })
    it('RECHECK_INTERVAL_MS = 12 hr', () => {
      expect(RECHECK_INTERVAL_MS).toBe(43200000)
    })
    it('IMMEDIATE_REFRESH_THRESHOLD_MS = 1 sec', () => {
      expect(IMMEDIATE_REFRESH_THRESHOLD_MS).toBe(1000)
    })
  })

  describe('decodeJwtPayload', () => {
    it('decodes standard token', () => {
      const tok = makeToken({ sub: '1', name: 'alice', exp: 9999 })
      const p = decodeJwtPayload(tok)!
      expect(p.sub).toBe('1')
      expect(p.name).toBe('alice')
      expect(p.exp).toBe(9999)
    })

    it('returns null when not 3 parts', () => {
      expect(decodeJwtPayload('a.b')).toBeNull()
      expect(decodeJwtPayload('a.b.c.d')).toBeNull()
    })

    it('returns null on bad base64', () => {
      const bad = 'header.!!!notbase64!!!.sig'
      expect(decodeJwtPayload(bad)).toBeNull()
    })

    it('uses cache on second call (same payload)', () => {
      const tok = makeToken({ sub: 'cached', exp: 5000 })
      const a = decodeJwtPayload(tok)
      const b = decodeJwtPayload(tok)
      expect(a).toBe(b)
    })

    it('returns null when JSON.parse fails', () => {
      // Build a base64url that decodes to invalid JSON
      const badJson = '#notjson!'
      const bad = btoa(badJson).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_')
      const tok = `aaa.${bad}.bbb-unique`
      expect(decodeJwtPayload(tok)).toBeNull()
    })

    it('handles cache eviction when > MAX_CACHE_SIZE (50)', () => {
      // Build 60 tokens, all different signatures -> different cache keys
      for (let i = 0; i < 60; i++) {
        const tok = makeToken({ sub: `u${i}`, exp: i + 1000 }, { alg: `A${i}` })
        decodeJwtPayload(tok)
      }
      // 60th token still decodes successfully (LRU evicted older)
      const last = makeToken({ sub: 'u59', exp: 9999 }, { alg: 'A59' })
      const p = decodeJwtPayload(last)
      expect(p?.sub).toBe('u59')
    })

    it('non-standard 3-part token still attempts to parse', () => {
      const tok = 'a.b.c'
      // parts[1] = 'b' which is not valid base64 url -> null
      expect(decodeJwtPayload(tok)).toBeNull()
    })
  })

  describe('getTokenExpiry', () => {
    it('returns exp * 1000', () => {
      const tok = makeToken({ exp: 100 })
      expect(getTokenExpiry(tok)).toBe(100000)
    })
    it('returns null when no exp', () => {
      const tok = makeToken({ sub: 'x' })
      expect(getTokenExpiry(tok)).toBeNull()
    })
    it('returns null for invalid token', () => {
      expect(getTokenExpiry('bad')).toBeNull()
    })
  })

  describe('getTimeUntilExpiry', () => {
    it('returns ms until exp', () => {
      const future = Math.floor(Date.now() / 1000) + 3600
      const tok = makeToken({ exp: future })
      const ms = getTimeUntilExpiry(tok)
      expect(ms).toBeGreaterThan(3500000)
      expect(ms).toBeLessThanOrEqual(3600000)
    })
    it('returns 0 when no exp', () => {
      const tok = makeToken({ sub: 'x' })
      expect(getTimeUntilExpiry(tok)).toBe(0)
    })
    it('returns 0 when expired', () => {
      const past = Math.floor(Date.now() / 1000) - 100
      const tok = makeToken({ exp: past })
      expect(getTimeUntilExpiry(tok)).toBe(0)
    })
  })

  describe('isTokenExpired', () => {
    it('true when exp in past', () => {
      const past = Math.floor(Date.now() / 1000) - 100
      expect(isTokenExpired(makeToken({ exp: past }))).toBe(true)
    })
    it('false when exp in future', () => {
      const future = Math.floor(Date.now() / 1000) + 1000
      expect(isTokenExpired(makeToken({ exp: future }))).toBe(false)
    })
    it('true when no exp (treats as 0)', () => {
      expect(isTokenExpired(makeToken({ sub: 'x' }))).toBe(true)
    })
  })

  describe('calculateRefreshDelay', () => {
    it('delay = max(until-refreshBefore, 0)', () => {
      expect(calculateRefreshDelay(1000, 100)).toBe(900)
    })
    it('clamped at 0 when until < refreshBefore', () => {
      expect(calculateRefreshDelay(50, 100)).toBe(0)
    })
    it('clamped at MAX_TIMEOUT_MS', () => {
      expect(calculateRefreshDelay(MAX_TIMEOUT_MS + 1000, 0)).toBe(MAX_TIMEOUT_MS)
    })
    it('default refreshBefore = 10 min', () => {
      const until = 11 * 60 * 1000  // 11 min
      const r = calculateRefreshDelay(until)
      expect(r).toBe(60 * 1000)  // 1 min remaining
    })
  })
})
