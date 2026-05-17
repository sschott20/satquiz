import { writable } from 'svelte/store';
import type { QuestionBank, SessionState, GradedSession } from './types';

export type AppScreen = 'setup' | 'session' | 'review';

export const screen = writable<AppScreen>('setup');
export const bank = writable<QuestionBank | null>(null);
export const session = writable<SessionState | null>(null);
export const graded = writable<GradedSession | null>(null);
