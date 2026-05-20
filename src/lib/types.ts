export type Section = 'rw' | 'math';
export type Difficulty = 'E' | 'M' | 'H';
export type QuestionType = 'mcq' | 'spr';
export type Choice = 'A' | 'B' | 'C' | 'D';

export type Question = {
  id: string;
  section: Section;
  domain: string;
  skill: string;
  difficulty: Difficulty;
  isActive: boolean;

  stimulus?: string;
  prompt: string;
  figure?: string;

  type: QuestionType;

  choices?: [string, string, string, string];
  correctChoice?: Choice;

  acceptedAnswers?: string[];

  explanation?: string;
};

export type QuestionBank = {
  version: string;
  generatedAt: string;
  questions: Question[];
};

export type SetupForm = {
  section: Section;
  count: number;
  timeLimitMin: number | null;
  difficulties: Difficulty[];
  excludeActive: boolean;
};

export const DEFAULT_SETUP: SetupForm = {
  section: 'math',
  count: 10,
  timeLimitMin: null,
  difficulties: ['E', 'M', 'H'],
  excludeActive: true,
};

export type PerQuestionState = {
  selectedChoice?: Choice;
  sprInput?: string;
  markedForReview: boolean;
  crossedOut: Choice[];
  timeSpentMs: number;
};

export type SessionState = {
  questions: Question[];
  perQuestion: PerQuestionState[];
  currentIndex: number;
  startedAt: number;
  timeLimitMs: number | null;
  endedAt?: number;
};

export type GradedQuestion = {
  question: Question;
  state: PerQuestionState;
  isCorrect: boolean;
  userAnswerDisplay: string;
  correctAnswerDisplay: string;
};

export type GradedSession = {
  graded: GradedQuestion[];
  score: number;
  total: number;
  totalTimeMs: number;
  byDomain: Record<string, { correct: number; total: number }>;
  bySkill: Record<string, { correct: number; total: number }>;
  byDifficulty: Record<Difficulty, { correct: number; total: number }>;
};

export type PerQuestionRecord = {
  id: string;
  firstAnswer: Choice | string | null;
  firstCorrect: boolean;
  correctedOnRetry: boolean;
  timeSpentMs: number;
  markedForReview: boolean;
};

export type SessionRecord = {
  startedAt: number;
  endedAt: number;
  setup: SetupForm;
  perQuestion: PerQuestionRecord[];
  score: number;
};
