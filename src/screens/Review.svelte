<script lang="ts">
  import { screen, graded, session } from '../lib/stores';
  import SessionResultTable from '../components/SessionResultTable.svelte';

  function fmtTime(ms: number): string {
    const total = Math.round(ms / 1000);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  }

  function newSession() {
    graded.set(null);
    session.set(null);
    screen.set('setup');
  }
</script>

{#if $graded}
  <main class="review">
    <header class="summary">
      <h1>Score: {$graded.score} / {$graded.total}</h1>
      <p>Total time: {fmtTime($graded.totalTimeMs)} · Avg per question:
        {fmtTime($graded.totalTimeMs / Math.max($graded.total, 1))}</p>
      <button class="primary" onclick={newSession}>Start new session</button>
    </header>

    <SessionResultTable graded={$graded} />
  </main>
{/if}

<style>
  .review { max-width: 60rem; margin: 1rem auto; padding: 1rem; background: white; border-radius: 8px; }
  .summary { display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-start; }
  .primary { background: #1a73e8; color: white; border: 0; padding: 0.5rem 1rem; border-radius: 4px; align-self: flex-start; }

  @media (max-width: 768px) {
    .review { margin: 0.5rem; padding: 0.75rem; border-radius: 6px; }
  }
</style>
