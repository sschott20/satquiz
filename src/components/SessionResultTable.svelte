<script lang="ts">
  import QuestionView from './QuestionView.svelte';
  import DrillRetry from './DrillRetry.svelte';
  import { sanitize, renderMathIn } from '../lib/sanitize';
  import type { Difficulty, GradedSession } from '../lib/types';

  type Props = {
    graded: GradedSession;
    drillEnabled?: boolean;
    resolved?: boolean[];
    onResolve?: (i: number) => void;
  };
  let { graded, drillEnabled = false, resolved = [], onResolve = () => {} }: Props = $props();

  let expanded = $state<number | null>(null);

  function fmtTime(ms: number): string {
    const total = Math.round(ms / 1000);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  }

  function explanationAction(node: HTMLElement, html: string) {
    function set(h: string) {
      node.innerHTML = sanitize(h);
      renderMathIn(node);
    }
    set(html);
    return { update: set };
  }

  function isHidden(i: number, isCorrect: boolean): boolean {
    if (!drillEnabled) return false;
    if (isCorrect) return false;
    return !resolved[i];
  }

  function rowMark(i: number, isCorrect: boolean): string {
    if (isCorrect) return '✓';
    if (drillEnabled && !resolved[i]) return '?';
    if (resolved[i]) return '✗ → ✓';
    return '✗';
  }
</script>

<section>
  <h2>Per question</h2>
  <table>
    <thead>
      <tr><th></th><th>#</th><th>Flag</th><th>Your</th><th>Correct</th><th>Time</th><th></th></tr>
    </thead>
    <tbody>
      {#each graded.graded as g, i}
        {@const hidden = isHidden(i, g.isCorrect)}
        <tr
          class:correct={g.isCorrect}
          class:wrong={!g.isCorrect && !resolved[i]}
          class:resolved={!g.isCorrect && resolved[i]}
          class:pending={hidden}
          onclick={() => (expanded = expanded === i ? null : i)}
          data-testid="result-row"
        >
          <td class="caret">{expanded === i ? '▾' : '▸'}</td>
          <td>{i + 1}</td>
          <td>{g.state.markedForReview ? '⚑' : ''}</td>
          <td>{g.userAnswerDisplay}</td>
          <td>{hidden ? '—' : g.correctAnswerDisplay}</td>
          <td>{fmtTime(g.state.timeSpentMs)}</td>
          <td>{rowMark(i, g.isCorrect)}</td>
        </tr>
        {#if expanded === i}
          <tr class="detail">
            <td colspan="7">
              <QuestionView question={g.question} pq={g.state} onUpdate={() => {}} readOnly />

              {#if hidden}
                <p class="hidden-note">
                  <em>Pick the correct answer below. The explanation will reveal once you get it right.</em>
                </p>
                <DrillRetry question={g.question} onResolve={() => onResolve(i)} />
              {:else}
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
      {@const v = graded.byDifficulty[d]}
      {#if v.total > 0}
        <li>{d}: {v.correct}/{v.total}</li>
      {/if}
    {/each}
  </ul>

  <h3>By domain</h3>
  <ul>
    {#each Object.entries(graded.byDomain) as [name, v]}
      <li>{name}: {v.correct}/{v.total}</li>
    {/each}
  </ul>

  <h3>By skill</h3>
  <ul>
    {#each Object.entries(graded.bySkill) as [name, v]}
      <li>{name}: {v.correct}/{v.total}</li>
    {/each}
  </ul>
</section>

<style>
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #eee; }
  tbody tr { cursor: pointer; }
  tr.correct td:last-child { color: #1b5e20; }
  tr.wrong td:last-child { color: #b32400; }
  tr.resolved td:last-child { color: #e65100; }
  tr.pending td:last-child { color: #6a1b9a; font-weight: 600; }
  tr.detail td { background: #fafafa; cursor: default; }
  .breakdown ul { padding-left: 1.25rem; }
  .explain { padding: 0.5rem 0; }
  .no-explain { color: #888; padding: 0.5rem 0; }
  .hidden-note { color: #555; padding: 0.5rem 0; }
  .caret { width: 1.5rem; color: #888; user-select: none; }

  @media (max-width: 768px) {
    table { font-size: 0.85rem; }
    th, td { padding: 0.35rem 0.3rem; }
    .caret { width: 1rem; }
    th:nth-child(3), td:nth-child(3) { display: none; }
  }
</style>
