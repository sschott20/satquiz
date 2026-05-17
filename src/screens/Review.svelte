<script lang="ts">
  import { screen, graded, session } from '../lib/stores';
  import { sanitize, renderMathIn } from '../lib/sanitize';
  import QuestionView from '../components/QuestionView.svelte';
  import type { Difficulty } from '../lib/types';

  let expanded = $state<number | null>(null);

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

  function explanationAction(node: HTMLElement, html: string) {
    function set(h: string) {
      node.innerHTML = sanitize(h);
      renderMathIn(node);
    }
    set(html);
    return { update: set };
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

    <section>
      <h2>Per question</h2>
      <table>
        <thead>
          <tr><th></th><th>#</th><th>Flag</th><th>Your</th><th>Correct</th><th>Time</th><th></th></tr>
        </thead>
        <tbody>
          {#each $graded.graded as g, i}
            <tr
              class:correct={g.isCorrect}
              class:wrong={!g.isCorrect}
              onclick={() => (expanded = expanded === i ? null : i)}
            >
              <td class="caret">{expanded === i ? '▾' : '▸'}</td>
              <td>{i + 1}</td>
              <td>{g.state.markedForReview ? '⚑' : ''}</td>
              <td>{g.userAnswerDisplay}</td>
              <td>{g.correctAnswerDisplay}</td>
              <td>{fmtTime(g.state.timeSpentMs)}</td>
              <td>{g.isCorrect ? '✓' : '✗'}</td>
            </tr>
            {#if expanded === i}
              <tr class="detail">
                <td colspan="7">
                  <QuestionView question={g.question} pq={g.state} onUpdate={() => {}} readOnly />
                  {#if g.question.explanation}
                    <h4>Explanation</h4>
                    <div
                      class="explain"
                      data-testid="explanation"
                      use:explanationAction={g.question.explanation}
                    ></div>
                  {:else}
                    <p class="no-explain"><em>No explanation available for this question.</em></p>
                  {/if}
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </section>

    <section class="breakdown">
      <h2>Breakdown</h2>

      <h3>By difficulty</h3>
      <ul>
        {#each (['E','M','H'] as Difficulty[]) as d}
          {@const v = $graded.byDifficulty[d]}
          {#if v.total > 0}
            <li>{d}: {v.correct}/{v.total}</li>
          {/if}
        {/each}
      </ul>

      <h3>By domain</h3>
      <ul>
        {#each Object.entries($graded.byDomain) as [name, v]}
          <li>{name}: {v.correct}/{v.total}</li>
        {/each}
      </ul>

      <h3>By skill</h3>
      <ul>
        {#each Object.entries($graded.bySkill) as [name, v]}
          <li>{name}: {v.correct}/{v.total}</li>
        {/each}
      </ul>
    </section>
  </main>
{/if}

<style>
  .review { max-width: 60rem; margin: 1rem auto; padding: 1rem; background: white; border-radius: 8px; }
  .summary { display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-start; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #eee; }
  tbody tr { cursor: pointer; }
  tr.correct td:last-child { color: #1b5e20; }
  tr.wrong td:last-child { color: #b32400; }
  tr.detail td { background: #fafafa; cursor: default; }
  .breakdown ul { padding-left: 1.25rem; }
  .primary { background: #1a73e8; color: white; border: 0; padding: 0.5rem 1rem; border-radius: 4px; align-self: flex-start; }
  .explain { padding: 0.5rem 0; }
  .no-explain { color: #888; padding: 0.5rem 0; }
  .caret { width: 1.5rem; color: #888; user-select: none; }

  @media (max-width: 768px) {
    .review { margin: 0.5rem; padding: 0.75rem; border-radius: 6px; }
    table { font-size: 0.85rem; }
    th, td { padding: 0.35rem 0.3rem; }
    .caret { width: 1rem; }
    /* Drop the "Flag" column on phones to save horizontal space. */
    th:nth-child(3), td:nth-child(3) { display: none; }
  }
</style>
