import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import DrillRetry from '../../src/components/DrillRetry.svelte';
import type { Question } from '../../src/lib/types';

afterEach(() => cleanup());

const mcq: Question = {
  id: 'q1', section: 'math', domain: 'd', skill: 's', difficulty: 'M',
  isActive: false, prompt: '<p>q?</p>', type: 'mcq',
  choices: ['a','b','c','d'], correctChoice: 'C',
};

const spr: Question = {
  id: 'q2', section: 'math', domain: 'd', skill: 's', difficulty: 'M',
  isActive: false, prompt: '<p>q?</p>', type: 'spr',
  acceptedAnswers: ['7', 'seven'],
};

describe('DrillRetry — MCQ', () => {
  it('does not resolve on wrong pick', async () => {
    const onResolve = vi.fn();
    render(DrillRetry, { props: { question: mcq, onResolve } });
    await fireEvent.click(screen.getByRole('button', { name: 'A' }));
    expect(onResolve).not.toHaveBeenCalled();
  });
  it('resolves on correct pick', async () => {
    const onResolve = vi.fn();
    render(DrillRetry, { props: { question: mcq, onResolve } });
    await fireEvent.click(screen.getByRole('button', { name: 'C' }));
    expect(onResolve).toHaveBeenCalledOnce();
  });
});

describe('DrillRetry — SPR', () => {
  it('does not resolve on wrong input', async () => {
    const onResolve = vi.fn();
    render(DrillRetry, { props: { question: spr, onResolve } });
    await fireEvent.input(screen.getByRole('textbox'), { target: { value: '1' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Check' }));
    expect(onResolve).not.toHaveBeenCalled();
  });
  it('resolves on a matching accepted answer', async () => {
    const onResolve = vi.fn();
    render(DrillRetry, { props: { question: spr, onResolve } });
    await fireEvent.input(screen.getByRole('textbox'), { target: { value: '7' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Check' }));
    expect(onResolve).toHaveBeenCalledOnce();
  });
  it('also matches a different equivalent form', async () => {
    const onResolve = vi.fn();
    render(DrillRetry, { props: { question: spr, onResolve } });
    await fireEvent.input(screen.getByRole('textbox'), { target: { value: 'seven' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Check' }));
    expect(onResolve).toHaveBeenCalledOnce();
  });
});
