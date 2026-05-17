import { describe, it, expect, beforeEach } from 'vitest';
import {
  loadDone, addDone, resetDone,
  loadSettings, saveSettings,
} from '../../src/lib/storage';
import { DEFAULT_SETUP } from '../../src/lib/types';

beforeEach(() => {
  localStorage.clear();
});

describe('done IDs', () => {
  it('starts empty', () => {
    expect(loadDone()).toEqual([]);
  });
  it('addDone unions with existing and dedupes', () => {
    addDone(['a', 'b']);
    addDone(['b', 'c']);
    expect(loadDone().sort()).toEqual(['a', 'b', 'c']);
  });
  it('resetDone clears the set', () => {
    addDone(['a', 'b']);
    resetDone();
    expect(loadDone()).toEqual([]);
  });
  it('persists in localStorage with version envelope', () => {
    addDone(['x']);
    expect(JSON.parse(localStorage.getItem('satquiz.done')!)).toEqual({
      version: 1, ids: ['x'],
    });
  });
});

describe('settings', () => {
  it('returns defaults if nothing saved', () => {
    expect(loadSettings()).toEqual(DEFAULT_SETUP);
  });
  it('saveSettings round-trips', () => {
    saveSettings({ ...DEFAULT_SETUP, count: 25, difficulties: ['H'] });
    expect(loadSettings()).toMatchObject({ count: 25, difficulties: ['H'] });
  });
  it('falls back to defaults if stored shape is corrupt', () => {
    localStorage.setItem('satquiz.settings', 'not json');
    expect(loadSettings()).toEqual(DEFAULT_SETUP);
  });
});
