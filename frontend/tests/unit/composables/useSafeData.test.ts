import { describe, it, expect } from 'vitest';
import { safeArray, safeObject, safeString, safeNumber } from '@/composables/useSafeData';

describe('useSafeData', () => {
  it('safeArray: null → []', () => {
    expect(safeArray(null)).toEqual([]);
  });
  it('safeArray: [1,2] → [1,2]', () => {
    expect(safeArray([1, 2])).toEqual([1, 2]);
  });
  it('safeArray: "not-array" → []', () => {
    expect(safeArray("not-array")).toEqual([]);
  });
  it('safeObject: null → fallback', () => {
    expect(safeObject(null, { default: true })).toEqual({ default: true });
  });
  it('safeObject: valid object preserved', () => {
    expect(safeObject({ a: 1 }, {})).toEqual({ a: 1 });
  });
  it('safeString: null → ""', () => {
    expect(safeString(null)).toBe("");
  });
  it('safeString: "hello" → "hello"', () => {
    expect(safeString("hello")).toBe("hello");
  });
  it('safeNumber: NaN → 0', () => {
    expect(safeNumber(NaN)).toBe(0);
  });
  it('safeNumber: undefined → 0', () => {
    expect(safeNumber(undefined)).toBe(0);
  });
  it('safeNumber: 42 → 42', () => {
    expect(safeNumber(42)).toBe(42);
  });
});
