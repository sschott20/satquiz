import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/svelte';
import NavigatorPopup from '../../src/components/NavigatorPopup.svelte';
import type { PerQuestionState } from '../../src/lib/types';

const s = (over: Partial<PerQuestionState> = {}): PerQuestionState =>
  ({ markedForReview: false, crossedOut: [], timeSpentMs: 0, ...over });

afterEach(() => cleanup());

describe('NavigatorPopup', () => {
  it('renders one button per question', () => {
    render(NavigatorPopup, {
      props: {
        perQuestion: [s(), s(), s()],
        currentIndex: 0,
        onJump: () => {},
        onClose: () => {},
      },
    });
    expect(screen.getAllByRole('button', { name: /Question \d+/ })).toHaveLength(3);
  });

  it('marks answered / unanswered / for-review states', () => {
    render(NavigatorPopup, {
      props: {
        perQuestion: [
          s({ selectedChoice: 'A' }),
          s({}),
          s({ sprInput: '3', markedForReview: true }),
        ],
        currentIndex: 0,
        onJump: () => {},
        onClose: () => {},
      },
    });
    const buttons = screen.getAllByRole('button', { name: /Question \d+/ });
    expect(buttons[0].className).toMatch(/answered/);
    expect(buttons[1].className).toMatch(/unanswered/);
    expect(buttons[2].className).toMatch(/flagged/);
  });

  it('calls onJump with index when a question is clicked', async () => {
    const onJump = vi.fn();
    render(NavigatorPopup, {
      props: {
        perQuestion: [s(), s(), s()],
        currentIndex: 0,
        onJump,
        onClose: () => {},
      },
    });
    await fireEvent.click(screen.getByRole('button', { name: 'Question 2' }));
    expect(onJump).toHaveBeenCalledWith(1);
  });
});
