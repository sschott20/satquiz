<script lang="ts">
  import { screen, graded, session, currentUser } from '../lib/stores';
  import { addDone, appendHistory, updateHistoryRecord } from '../lib/profile';
  import SessionResultTable from '../components/SessionResultTable.svelte';
  import type { PerQuestionRecord, SessionRecord } from '../lib/types';
  import { onMount } from 'svelte';

  let resolved = $state<boolean[]>([]);
  let committedAt = $state<number | null>(null);

  function fmtTime(ms: number): string {
    const total = Math.round(ms / 1000);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  }

  function buildRecord(): SessionRecord {
    const g = $graded!;
    const s = $session!;
    const per: PerQuestionRecord[] = g.graded.map((gq, i) => {
      const ans = gq.question.type === 'mcq'
        ? (gq.state.selectedChoice ?? null)
        : (gq.state.sprInput ?? null);
      return {
        id: gq.question.id,
        firstAnswer: ans,
        firstCorrect: gq.isCorrect,
        correctedOnRetry: !gq.isCorrect && !!resolved[i],
        timeSpentMs: gq.state.timeSpentMs,
        markedForReview: gq.state.markedForReview,
      };
    });
    return {
      startedAt: s.startedAt,
      endedAt: s.endedAt ?? Date.now(),
      setup: {
        section: s.questions[0]?.section ?? 'math',
        count: s.questions.length,
        timeLimitMin: s.timeLimitMs == null ? null : Math.round(s.timeLimitMs / 60_000),
        difficulties: ['E', 'M', 'H'],
        excludeActive: true,
      },
      perQuestion: per,
      score: g.score,
    };
  }

  onMount(() => {
    if (!$graded || !$session || !$currentUser) return;
    resolved = $graded.graded.map(() => false);
    addDone($session.questions.map((q) => q.id));
    const record = buildRecord();
    appendHistory(record);
    committedAt = record.startedAt;
  });

  function handleResolve(i: number) {
    resolved[i] = true;
    if (committedAt != null) {
      updateHistoryRecord(committedAt, (r) => ({
        ...r,
        perQuestion: r.perQuestion.map((p, j) =>
          j === i ? { ...p, correctedOnRetry: true } : p,
        ),
      }));
    }
  }

  function newSession() {
    graded.set(null);
    session.set(null);
    screen.set('setup');
  }

  function gotoHistory() {
    graded.set(null);
    session.set(null);
    screen.set('history');
  }

  const wrongCount = $derived($graded ? $graded.graded.filter((g) => !g.isCorrect).length : 0);
  const drilledCount = $derived(resolved.filter(Boolean).length);
</script>

{#if $graded}
  <main class="review">
    <header class="summary">
      <h1>Score: {$graded.score} / {$graded.total}</h1>
      {#if wrongCount > 0}
        <p class="drill-stat">Drilled to correct: {drilledCount} / {wrongCount}</p>
      {/if}
      <p>Total time: {fmtTime($graded.totalTimeMs)} · Avg per question:
        {fmtTime($graded.totalTimeMs / Math.max($graded.total, 1))}</p>
      <div class="actions">
        <button class="primary" onclick={newSession}>Start new session</button>
        <button class="ghost" onclick={gotoHistory}>History</button>
      </div>
    </header>

    <SessionResultTable
      graded={$graded}
      drillEnabled={true}
      {resolved}
      onResolve={handleResolve}
    />
  </main>
{/if}

<style>
  .review { max-width: 60rem; margin: 1rem auto; padding: 1rem; background: white; border-radius: 8px; }
  .summary { display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-start; }
  .drill-stat { color: #e65100; margin: 0; }
  .actions { display: flex; gap: 0.5rem; }
  .primary { background: #1a73e8; color: white; border: 0; padding: 0.5rem 1rem; border-radius: 4px; }
  .ghost { background: transparent; border: 1px solid #ccc; padding: 0.5rem 1rem; border-radius: 4px; }

  @media (max-width: 768px) {
    .review { margin: 0.5rem; padding: 0.75rem; border-radius: 6px; }
    .actions { flex-direction: column; width: 100%; }
    .actions button { width: 100%; }
  }
</style>
