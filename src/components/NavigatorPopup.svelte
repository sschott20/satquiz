<script lang="ts">
  import type { PerQuestionState } from '../lib/types';

  type Props = {
    perQuestion: PerQuestionState[];
    currentIndex: number;
    onJump: (i: number) => void;
    onClose: () => void;
  };
  let { perQuestion, currentIndex, onJump, onClose }: Props = $props();

  function statusClass(s: PerQuestionState): string {
    const answered = s.selectedChoice !== undefined || (s.sprInput?.trim()?.length ?? 0) > 0;
    if (s.markedForReview) return 'flagged';
    return answered ? 'answered' : 'unanswered';
  }
</script>

<div class="backdrop" role="presentation" onclick={onClose}></div>
<div class="popup" role="dialog" aria-label="Question navigator">
  <h2>Questions</h2>
  <div class="grid">
    {#each perQuestion as s, i}
      <button
        class={statusClass(s) + (i === currentIndex ? ' current' : '')}
        aria-label="Question {i + 1}"
        onclick={() => onJump(i)}
      >
        {i + 1}{#if s.markedForReview} ⚑{/if}
      </button>
    {/each}
  </div>
  <button class="close" onclick={onClose}>Close</button>
</div>

<style>
  .backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.2); }
  .popup { position: fixed; top: 4rem; left: 50%; transform: translateX(-50%);
    background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); min-width: 20rem; }
  .grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.4rem; margin: 0.5rem 0; }
  .grid button { padding: 0.5rem; border: 1px solid #ccc; background: white; border-radius: 4px; }
  .grid .answered { background: #e8f0fe; border-color: #1a73e8; }
  .grid .unanswered { background: white; }
  .grid .flagged { background: #fff59d; border-color: #f9a825; }
  .grid .current { outline: 2px solid #1a73e8; }
  .close { margin-top: 0.5rem; }
</style>
