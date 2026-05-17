<script lang="ts">
  import { sanitize, renderMathIn } from '../lib/sanitize';
  import type { Choice } from '../lib/types';

  type Props = {
    letter: Choice;
    html: string;
    selected: boolean;
    crossedOut: boolean;
    onSelect: () => void;
    onToggleCross: () => void;
  };
  let { letter, html, selected, crossedOut, onSelect, onToggleCross }: Props = $props();

  let bodyEl: HTMLDivElement | undefined = $state();
  $effect(() => {
    if (bodyEl) {
      bodyEl.innerHTML = sanitize(html);
      renderMathIn(bodyEl);
    }
  });
</script>

<div class="row" class:selected class:crossed={crossedOut}>
  <button class="letter" aria-pressed={selected} onclick={onSelect}>{letter}</button>
  <div class="body" bind:this={bodyEl}></div>
  <button class="cross" aria-label="Cross out choice {letter}" onclick={onToggleCross}>
    {crossedOut ? 'Undo' : 'Cross out'}
  </button>
</div>

<style>
  .row { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem;
    border: 1px solid #ddd; border-radius: 4px; margin: 0.25rem 0; }
  .row.selected { border-color: #1a73e8; background: #e8f0fe; }
  .row.crossed .body { text-decoration: line-through; color: #888; }
  .letter { width: 2rem; height: 2rem; border-radius: 50%; border: 1px solid #888; background: white; }
  .row.selected .letter { background: #1a73e8; color: white; border-color: #1a73e8; }
  .body { flex: 1; }
  .cross { font-size: 0.85rem; background: transparent; border: 1px solid #ccc; padding: 0.25rem 0.5rem; border-radius: 4px; }
</style>
