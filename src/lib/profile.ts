import { DEFAULT_SETUP, type SessionRecord, type SetupForm } from './types';

const USERS_KEY = 'satquiz.users';
const ACTIVE_KEY = 'satquiz.activeUser';
const VERSION = 1;
const HISTORY_CAP = 200;

const LEGACY_DONE = 'satquiz.done';
const LEGACY_SETTINGS = 'satquiz.settings';

export function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40);
}

function readJSON<T>(key: string, fallback: T): T {
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJSON(key: string, value: unknown): void {
  localStorage.setItem(key, JSON.stringify(value));
}

function doneKey(slug: string): string { return `satquiz.u.${slug}.done`; }
function settingsKey(slug: string): string { return `satquiz.u.${slug}.settings`; }
function historyKey(slug: string): string { return `satquiz.u.${slug}.history`; }

function requireActiveSlug(): string {
  const name = activeUser();
  if (!name) throw new Error('No active user. Call setActiveUser first.');
  return slugify(name);
}

export function listUsers(): string[] {
  return readJSON<string[]>(USERS_KEY, []);
}

export function activeUser(): string | null {
  return localStorage.getItem(ACTIVE_KEY);
}

export function createUser(name: string): void {
  const slug = slugify(name);
  if (!slug) return;
  const users = listUsers();
  const exists = users.some((u) => slugify(u) === slug);
  if (!exists) {
    users.push(name);
    writeJSON(USERS_KEY, users);
  }
}

export function setActiveUser(name: string): void {
  createUser(name);
  localStorage.setItem(ACTIVE_KEY, name);
}

export function deleteUser(name: string): void {
  const slug = slugify(name);
  if (!slug) return;
  localStorage.removeItem(doneKey(slug));
  localStorage.removeItem(settingsKey(slug));
  localStorage.removeItem(historyKey(slug));
  const users = listUsers().filter((u) => slugify(u) !== slug);
  writeJSON(USERS_KEY, users);
  const current = activeUser();
  if (current && slugify(current) === slug) {
    localStorage.removeItem(ACTIVE_KEY);
  }
}

type DonePayload = { version: number; ids: string[] };
type SettingsPayload = { version: number; settings: SetupForm };
type HistoryPayload = { version: number; records: SessionRecord[] };

export function loadDone(): string[] {
  const slug = requireActiveSlug();
  const p = readJSON<DonePayload | null>(doneKey(slug), null);
  if (!p || p.version !== VERSION || !Array.isArray(p.ids)) return [];
  return p.ids;
}

export function addDone(ids: string[]): void {
  const slug = requireActiveSlug();
  const set = new Set(loadDone());
  for (const id of ids) set.add(id);
  writeJSON(doneKey(slug), { version: VERSION, ids: [...set].sort() });
}

export function resetDone(): void {
  const slug = requireActiveSlug();
  localStorage.removeItem(doneKey(slug));
}

export function loadSettings(): SetupForm {
  const slug = requireActiveSlug();
  const p = readJSON<SettingsPayload | null>(settingsKey(slug), null);
  if (!p || p.version !== VERSION) return { ...DEFAULT_SETUP };
  return { ...DEFAULT_SETUP, ...p.settings };
}

export function saveSettings(s: SetupForm): void {
  const slug = requireActiveSlug();
  writeJSON(settingsKey(slug), { version: VERSION, settings: s });
}

export function loadHistory(): SessionRecord[] {
  const slug = requireActiveSlug();
  const p = readJSON<HistoryPayload | null>(historyKey(slug), null);
  if (!p || p.version !== VERSION || !Array.isArray(p.records)) return [];
  return p.records;
}

export function appendHistory(record: SessionRecord): void {
  const slug = requireActiveSlug();
  const all = loadHistory();
  all.push(record);
  while (all.length > HISTORY_CAP) all.shift();
  writeJSON(historyKey(slug), { version: VERSION, records: all });
}

export function updateHistoryRecord(startedAt: number, mut: (r: SessionRecord) => SessionRecord): void {
  const slug = requireActiveSlug();
  const all = loadHistory();
  const idx = all.findIndex((r) => r.startedAt === startedAt);
  if (idx === -1) return;
  all[idx] = mut(all[idx]);
  writeJSON(historyKey(slug), { version: VERSION, records: all });
}

export function clearHistory(): void {
  const slug = requireActiveSlug();
  localStorage.removeItem(historyKey(slug));
}

export function migrateLegacy(intoUser: string): void {
  const slug = slugify(intoUser);
  if (!slug) return;

  const legacyDone = readJSON<DonePayload | null>(LEGACY_DONE, null);
  if (legacyDone?.version === VERSION && Array.isArray(legacyDone.ids)) {
    const prev = readJSON<DonePayload | null>(doneKey(slug), null);
    const merged = new Set<string>([
      ...(prev?.ids ?? []),
      ...legacyDone.ids,
    ]);
    writeJSON(doneKey(slug), { version: VERSION, ids: [...merged].sort() });
    localStorage.removeItem(LEGACY_DONE);
  }

  const legacySettings = readJSON<SettingsPayload | null>(LEGACY_SETTINGS, null);
  if (legacySettings?.version === VERSION) {
    writeJSON(settingsKey(slug), { version: VERSION, settings: legacySettings.settings });
    localStorage.removeItem(LEGACY_SETTINGS);
  }
}

export function hasLegacyData(): boolean {
  return !!localStorage.getItem(LEGACY_DONE) || !!localStorage.getItem(LEGACY_SETTINGS);
}
