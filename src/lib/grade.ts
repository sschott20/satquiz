import { matchesSpr } from './math';
import type {
  Difficulty, GradedQuestion, GradedSession, PerQuestionState,
  Question, SessionState,
} from './types';

function isCorrect(q: Question, s: PerQuestionState): boolean {
  if (q.type === 'mcq') {
    return !!s.selectedChoice && s.selectedChoice === q.correctChoice;
  }
  if (q.type === 'spr') {
    return !!s.sprInput && matchesSpr(s.sprInput, q.acceptedAnswers ?? []);
  }
  return false;
}

function userDisplay(q: Question, s: PerQuestionState): string {
  if (q.type === 'mcq') return s.selectedChoice ?? '—';
  if (q.type === 'spr') return s.sprInput?.trim() || '—';
  return '—';
}

function correctDisplay(q: Question): string {
  if (q.type === 'mcq') return q.correctChoice ?? '—';
  if (q.type === 'spr') return (q.acceptedAnswers ?? []).join(' or ');
  return '—';
}

export function gradeSession(session: SessionState): GradedSession {
  const graded: GradedQuestion[] = session.questions.map((q, i) => {
    const state = session.perQuestion[i];
    return {
      question: q,
      state,
      isCorrect: isCorrect(q, state),
      userAnswerDisplay: userDisplay(q, state),
      correctAnswerDisplay: correctDisplay(q),
    };
  });

  const byDomain: Record<string, { correct: number; total: number }> = {};
  const bySkill: Record<string, { correct: number; total: number }> = {};
  const byDifficulty: Record<Difficulty, { correct: number; total: number }> = {
    E: { correct: 0, total: 0 },
    M: { correct: 0, total: 0 },
    H: { correct: 0, total: 0 },
  };

  for (const g of graded) {
    const inc = (m: Record<string, { correct: number; total: number }>, k: string) => {
      m[k] ??= { correct: 0, total: 0 };
      m[k].total += 1;
      if (g.isCorrect) m[k].correct += 1;
    };
    inc(byDomain, g.question.domain);
    inc(bySkill, g.question.skill);
    byDifficulty[g.question.difficulty].total += 1;
    if (g.isCorrect) byDifficulty[g.question.difficulty].correct += 1;
  }

  return {
    graded,
    score: graded.filter((g) => g.isCorrect).length,
    total: graded.length,
    totalTimeMs: session.perQuestion.reduce((s, q) => s + q.timeSpentMs, 0),
    byDomain,
    bySkill,
    byDifficulty,
  };
}
