import { describe, it, expect } from 'vitest';
import { matchesSpr, normalizeSprInput } from '../../src/lib/math';

describe('normalizeSprInput', () => {
  it('trims whitespace', () => {
    expect(normalizeSprInput('  3 ')).toBe('3');
  });
  it('removes leading + sign', () => {
    expect(normalizeSprInput('+3')).toBe('3');
  });
  it('preserves negative sign and decimals', () => {
    expect(normalizeSprInput('-0.5')).toBe('-0.5');
  });
});

describe('matchesSpr', () => {
  it('returns true on exact match', () => {
    expect(matchesSpr('3', ['3'])).toBe(true);
  });
  it('matches across whitespace differences', () => {
    expect(matchesSpr(' 3 ', ['3'])).toBe(true);
  });
  it('matches any of multiple accepted forms', () => {
    expect(matchesSpr('0.5', ['1/2', '0.5', '.5'])).toBe(true);
    expect(matchesSpr('.5', ['1/2', '0.5', '.5'])).toBe(true);
  });
  it('returns false on no match', () => {
    expect(matchesSpr('4', ['3'])).toBe(false);
  });
  it('returns false on empty input', () => {
    expect(matchesSpr('', ['3'])).toBe(false);
    expect(matchesSpr('   ', ['3'])).toBe(false);
  });
});
