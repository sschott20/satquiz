import { DEFAULT_SETUP, type SetupForm } from './types';

const DONE_KEY = 'satquiz.done';
const SETTINGS_KEY = 'satquiz.settings';
const VERSION = 1;

type DonePayload = { version: number; ids: string[] };
type SettingsPayload = { version: number; settings: SetupForm };

export function loadDone(): string[] {
  const raw = localStorage.getItem(DONE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as DonePayload;
    if (parsed?.version !== VERSION || !Array.isArray(parsed.ids)) return [];
    return parsed.ids;
  } catch {
    return [];
  }
}

export function addDone(ids: string[]): void {
  const existing = new Set(loadDone());
  for (const id of ids) existing.add(id);
  const next: DonePayload = { version: VERSION, ids: [...existing].sort() };
  localStorage.setItem(DONE_KEY, JSON.stringify(next));
}

export function resetDone(): void {
  localStorage.removeItem(DONE_KEY);
}

export function loadSettings(): SetupForm {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (!raw) return DEFAULT_SETUP;
  try {
    const parsed = JSON.parse(raw) as SettingsPayload;
    if (parsed?.version !== VERSION) return DEFAULT_SETUP;
    return { ...DEFAULT_SETUP, ...parsed.settings };
  } catch {
    return DEFAULT_SETUP;
  }
}

export function saveSettings(settings: SetupForm): void {
  const payload: SettingsPayload = { version: VERSION, settings };
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(payload));
}
