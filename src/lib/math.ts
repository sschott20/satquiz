export function normalizeSprInput(input: string): string {
  const trimmed = input.trim();
  if (trimmed.startsWith('+')) return trimmed.slice(1);
  return trimmed;
}

export function matchesSpr(input: string, accepted: string[]): boolean {
  const norm = normalizeSprInput(input);
  if (norm === '') return false;
  return accepted.some((a) => normalizeSprInput(a) === norm);
}
