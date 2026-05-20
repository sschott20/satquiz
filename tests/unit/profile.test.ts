import { describe, it, expect, beforeEach } from 'vitest';
import {
  slugify, listUsers, activeUser, setActiveUser, createUser, deleteUser,
  loadDone, addDone, resetDone,
  loadSettings, saveSettings,
  loadHistory, appendHistory, clearHistory,
  migrateLegacy,
} from '../../src/lib/profile';
import { DEFAULT_SETUP, type SessionRecord } from '../../src/lib/types';

beforeEach(() => {
  localStorage.clear();
});

describe('slugify', () => {
  it('lowercases and replaces non-alphanumerics with -', () => {
    expect(slugify('Alex Schott')).toBe('alex-schott');
    expect(slugify('  Hello!  World ')).toBe('hello-world');
  });
  it('trims to 40 chars', () => {
    expect(slugify('a'.repeat(60)).length).toBe(40);
  });
  it('treats case-different names as the same slug', () => {
    expect(slugify('ALEX')).toBe(slugify('alex'));
  });
});

describe('users list and active user', () => {
  it('starts with no users and no active user', () => {
    expect(listUsers()).toEqual([]);
    expect(activeUser()).toBeNull();
  });
  it('createUser adds to the list', () => {
    createUser('Alex');
    expect(listUsers()).toEqual(['Alex']);
  });
  it('createUser dedupes by slug, preserving original display name', () => {
    createUser('Alex');
    createUser('ALEX');
    expect(listUsers()).toEqual(['Alex']);
  });
  it('setActiveUser creates if missing and sets active', () => {
    setActiveUser('Bea');
    expect(activeUser()).toBe('Bea');
    expect(listUsers()).toEqual(['Bea']);
  });
  it('deleteUser removes user and clears their keys', () => {
    setActiveUser('Cy');
    addDone(['q1']);
    saveSettings({ ...DEFAULT_SETUP, count: 7 });
    deleteUser('Cy');
    expect(listUsers()).toEqual([]);
    expect(localStorage.getItem('satquiz.u.cy.done')).toBeNull();
    expect(localStorage.getItem('satquiz.u.cy.settings')).toBeNull();
    expect(activeUser()).toBeNull();
  });
});

describe('per-user done', () => {
  it('round-trips and dedupes', () => {
    setActiveUser('Alex');
    addDone(['a', 'b']);
    addDone(['b', 'c']);
    expect(loadDone().sort()).toEqual(['a', 'b', 'c']);
  });
  it('is isolated per user', () => {
    setActiveUser('Alex');
    addDone(['a']);
    setActiveUser('Bea');
    expect(loadDone()).toEqual([]);
    addDone(['b']);
    setActiveUser('Alex');
    expect(loadDone()).toEqual(['a']);
  });
  it('resetDone clears just the active user', () => {
    setActiveUser('Alex');
    addDone(['a']);
    setActiveUser('Bea');
    addDone(['b']);
    resetDone();
    expect(loadDone()).toEqual([]);
    setActiveUser('Alex');
    expect(loadDone()).toEqual(['a']);
  });
});

describe('per-user settings', () => {
  it('returns defaults if nothing saved', () => {
    setActiveUser('Alex');
    expect(loadSettings()).toEqual(DEFAULT_SETUP);
  });
  it('round-trips', () => {
    setActiveUser('Alex');
    saveSettings({ ...DEFAULT_SETUP, count: 5, timeLimitMin: null });
    expect(loadSettings().count).toBe(5);
    expect(loadSettings().timeLimitMin).toBeNull();
  });
});

describe('history', () => {
  const r = (startedAt: number): SessionRecord => ({
    startedAt, endedAt: startedAt + 1000, setup: DEFAULT_SETUP,
    perQuestion: [], score: 0,
  });

  it('appendHistory orders newest-last and caps at 200', () => {
    setActiveUser('Alex');
    for (let i = 0; i < 205; i++) appendHistory(r(i));
    const h = loadHistory();
    expect(h.length).toBe(200);
    expect(h[0].startedAt).toBe(5);
    expect(h[199].startedAt).toBe(204);
  });
  it('clearHistory empties', () => {
    setActiveUser('Alex');
    appendHistory(r(1));
    clearHistory();
    expect(loadHistory()).toEqual([]);
  });
});

describe('migrateLegacy', () => {
  it('moves legacy satquiz.done and satquiz.settings under a user', () => {
    localStorage.setItem('satquiz.done', JSON.stringify({ version: 1, ids: ['old1', 'old2'] }));
    localStorage.setItem('satquiz.settings', JSON.stringify({
      version: 1, settings: { ...DEFAULT_SETUP, count: 42 },
    }));
    setActiveUser('Alex');
    migrateLegacy('Alex');
    expect(loadDone().sort()).toEqual(['old1', 'old2']);
    expect(loadSettings().count).toBe(42);
    expect(localStorage.getItem('satquiz.done')).toBeNull();
    expect(localStorage.getItem('satquiz.settings')).toBeNull();
  });
  it('is a no-op when no legacy keys exist', () => {
    setActiveUser('Alex');
    migrateLegacy('Alex');
    expect(loadDone()).toEqual([]);
  });
  it('unions legacy done into existing user done', () => {
    setActiveUser('Alex');
    addDone(['new1']);
    localStorage.setItem('satquiz.done', JSON.stringify({ version: 1, ids: ['old1'] }));
    migrateLegacy('Alex');
    expect(loadDone().sort()).toEqual(['new1', 'old1']);
  });
});
