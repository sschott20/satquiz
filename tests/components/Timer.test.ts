import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/svelte';
import Timer from '../../src/components/Timer.svelte';

beforeEach(() => { vi.useFakeTimers(); });
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe('Timer', () => {
  it('shows initial mm:ss', () => {
    const startedAt = Date.now();
    render(Timer, { props: { startedAt, totalMs: 65_000, onExpire: () => {} } });
    expect(screen.getByTestId('timer').textContent?.trim()).toBe('01:05');
  });

  it('ticks down', async () => {
    const startedAt = Date.now();
    render(Timer, { props: { startedAt, totalMs: 5_000, onExpire: () => {} } });
    await vi.advanceTimersByTimeAsync(2_000);
    expect(screen.getByTestId('timer').textContent?.trim()).toBe('00:03');
  });

  it('calls onExpire at zero', async () => {
    const startedAt = Date.now();
    const onExpire = vi.fn();
    render(Timer, { props: { startedAt, totalMs: 1_000, onExpire } });
    await vi.advanceTimersByTimeAsync(1_500);
    expect(onExpire).toHaveBeenCalledOnce();
  });

  it('hides time when hidden=true', () => {
    const startedAt = Date.now();
    render(Timer, { props: { startedAt, totalMs: 60_000, hidden: true, onExpire: () => {} } });
    expect(screen.getByTestId('timer').textContent?.trim()).toBe('Time hidden');
  });
});
