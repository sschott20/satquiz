import { describe, it, expect } from 'vitest';
import { filterMatching, sampleQuestions } from '../../src/lib/filter';
import type { Question, SetupForm } from '../../src/lib/types';

const q = (over: Partial<Question>): Question => ({
  id: 'x', section: 'math', domain: 'd', skill: 's', difficulty: 'M',
  isActive: false, prompt: '', type: 'mcq',
  choices: ['a', 'b', 'c', 'd'], correctChoice: 'A',
  ...over,
});

const setup = (over: Partial<SetupForm> = {}): SetupForm => ({
  section: 'math', count: 10, timeLimitMin: 15,
  difficulties: ['E', 'M', 'H'], excludeActive: false, ...over,
});

describe('filterMatching', () => {
  const bank: Question[] = [
    q({ id: '1', section: 'math', difficulty: 'E', isActive: false }),
    q({ id: '2', section: 'math', difficulty: 'M', isActive: true }),
    q({ id: '3', section: 'math', difficulty: 'H', isActive: false }),
    q({ id: '4', section: 'rw',   difficulty: 'E', isActive: false }),
  ];

  it('filters by section', () => {
    const out = filterMatching(bank, setup({ section: 'rw' }), []);
    expect(out.map(x => x.id)).toEqual(['4']);
  });
  it('filters by difficulty subset', () => {
    const out = filterMatching(bank, setup({ difficulties: ['H'] }), []);
    expect(out.map(x => x.id)).toEqual(['3']);
  });
  it('excludes active when excludeActive=true', () => {
    const out = filterMatching(bank, setup({ excludeActive: true }), []);
    expect(out.map(x => x.id).sort()).toEqual(['1', '3']);
  });
  it('excludes already-done IDs', () => {
    const out = filterMatching(bank, setup(), ['1', '3']);
    expect(out.map(x => x.id)).toEqual(['2']);
  });
});

describe('sampleQuestions', () => {
  const big: Question[] = Array.from({ length: 50 }, (_, i) =>
    q({ id: String(i) }),
  );
  it('returns at most count items', () => {
    const out = sampleQuestions(big, 10, () => 0.5);
    expect(out.length).toBe(10);
  });
  it('returns all if fewer than count', () => {
    const out = sampleQuestions(big.slice(0, 3), 10, () => 0.5);
    expect(out.length).toBe(3);
  });
  it('is deterministic given a seeded rng', () => {
    const seed = () => 0.42;
    const a = sampleQuestions(big, 5, seed).map(x => x.id);
    const b = sampleQuestions(big, 5, seed).map(x => x.id);
    expect(a).toEqual(b);
  });
  it('shuffles (different rng → different order)', () => {
    const a = sampleQuestions(big, 50, () => 0.0).map(x => x.id);
    const b = sampleQuestions(big, 50, () => 0.99).map(x => x.id);
    expect(a).not.toEqual(b);
  });
});
