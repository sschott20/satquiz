import { describe, it, expect } from 'vitest';
import { gradeSession } from '../../src/lib/grade';
import type { Question, SessionState, PerQuestionState } from '../../src/lib/types';

const mcq = (over: Partial<Question>): Question => ({
  id: 'x', section: 'math', domain: 'Algebra', skill: 'Linear', difficulty: 'M',
  isActive: false, prompt: '', type: 'mcq',
  choices: ['a', 'b', 'c', 'd'], correctChoice: 'B',
  ...over,
});
const spr = (over: Partial<Question>): Question => ({
  id: 'x', section: 'math', domain: 'Algebra', skill: 'Linear', difficulty: 'M',
  isActive: false, prompt: '', type: 'spr', acceptedAnswers: ['3'], ...over,
});
const state = (over: Partial<PerQuestionState> = {}): PerQuestionState => ({
  markedForReview: false, crossedOut: [], timeSpentMs: 1000, ...over,
});

describe('gradeSession', () => {
  it('scores MCQ correctness', () => {
    const session: SessionState = {
      questions: [mcq({ id: '1', correctChoice: 'B' }), mcq({ id: '2', correctChoice: 'C' })],
      perQuestion: [state({ selectedChoice: 'B' }), state({ selectedChoice: 'A' })],
      currentIndex: 0, startedAt: 0, timeLimitMs: 900000,
    };
    const out = gradeSession(session);
    expect(out.score).toBe(1);
    expect(out.total).toBe(2);
    expect(out.graded[0].isCorrect).toBe(true);
    expect(out.graded[1].isCorrect).toBe(false);
  });

  it('scores SPR with normalization', () => {
    const session: SessionState = {
      questions: [spr({ id: '1', acceptedAnswers: ['1/2', '0.5'] })],
      perQuestion: [state({ sprInput: ' 0.5 ' })],
      currentIndex: 0, startedAt: 0, timeLimitMs: 900000,
    };
    expect(gradeSession(session).score).toBe(1);
  });

  it('marks unanswered as wrong', () => {
    const session: SessionState = {
      questions: [mcq({ id: '1' })],
      perQuestion: [state({})],
      currentIndex: 0, startedAt: 0, timeLimitMs: 900000,
    };
    const out = gradeSession(session);
    expect(out.score).toBe(0);
    expect(out.graded[0].userAnswerDisplay).toBe('—');
  });

  it('aggregates by domain, skill, difficulty', () => {
    const session: SessionState = {
      questions: [
        mcq({ id: '1', domain: 'Algebra',  skill: 'Linear',    difficulty: 'E', correctChoice: 'A' }),
        mcq({ id: '2', domain: 'Algebra',  skill: 'Linear',    difficulty: 'M', correctChoice: 'B' }),
        mcq({ id: '3', domain: 'Geometry', skill: 'Triangles', difficulty: 'E', correctChoice: 'C' }),
      ],
      perQuestion: [
        state({ selectedChoice: 'A' }),
        state({ selectedChoice: 'D' }),
        state({ selectedChoice: 'C' }),
      ],
      currentIndex: 0, startedAt: 0, timeLimitMs: 900000,
    };
    const out = gradeSession(session);
    expect(out.byDomain['Algebra']).toEqual({ correct: 1, total: 2 });
    expect(out.byDomain['Geometry']).toEqual({ correct: 1, total: 1 });
    expect(out.bySkill['Linear']).toEqual({ correct: 1, total: 2 });
    expect(out.byDifficulty['E']).toEqual({ correct: 2, total: 2 });
    expect(out.byDifficulty['M']).toEqual({ correct: 0, total: 1 });
    expect(out.byDifficulty['H']).toEqual({ correct: 0, total: 0 });
  });

  it('sums total time', () => {
    const session: SessionState = {
      questions: [mcq({ id: '1' }), mcq({ id: '2' })],
      perQuestion: [state({ timeSpentMs: 1234 }), state({ timeSpentMs: 5678 })],
      currentIndex: 0, startedAt: 0, timeLimitMs: 900000,
    };
    expect(gradeSession(session).totalTimeMs).toBe(1234 + 5678);
  });
});
