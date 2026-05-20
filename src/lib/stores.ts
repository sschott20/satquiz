import { writable } from 'svelte/store';
import type { QuestionBank, SessionState, GradedSession } from './types';
import { activeUser } from './profile';

export type AppScreen = 'setup' | 'session' | 'review' | 'history';

export const screen = writable<AppScreen>('setup');
export const bank = writable<QuestionBank | null>(null);
export const session = writable<SessionState | null>(null);
export const graded = writable<GradedSession | null>(null);

export const currentUser = writable<string | null>(activeUser());
