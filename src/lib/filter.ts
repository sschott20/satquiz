import type { Question, SetupForm } from './types';

export function filterMatching(
  bank: Question[],
  setup: SetupForm,
  done: string[],
): Question[] {
  const doneSet = new Set(done);
  const diffSet = new Set(setup.difficulties);
  return bank.filter((q) =>
    q.section === setup.section &&
    diffSet.has(q.difficulty) &&
    (!setup.excludeActive || !q.isActive) &&
    !doneSet.has(q.id),
  );
}

export function sampleQuestions(
  pool: Question[],
  count: number,
  rng: () => number = Math.random,
): Question[] {
  const arr = pool.slice();
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr.slice(0, count);
}
