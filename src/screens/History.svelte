<script lang="ts">
  import { screen, currentUser, bank } from '../lib/stores';
  import { loadHistory, resetDone, clearHistory, deleteUser } from '../lib/profile';
  import { gradeSession } from '../lib/grade';
  import SessionResultTable from '../components/SessionResultTable.svelte';
  import QuestionView from '../components/QuestionView.svelte';
  import { sanitize, renderMathIn } from '../lib/sanitize';
  import type {
    PerQuestionRecord, PerQuestionState, Question, SessionRecord, SessionState,
  } from '../lib/types';

  type Tab = 'sessions' | 'all';
  let tab = $state<Tab>('sessions');

  let history = $state<SessionRecord[]>(loadHistory());
  let expandedSession = $state<number | null>(null);
  let expandedQuestion = $state<string | null>(null);

  const sessionsDesc = $derived([...history].sort((a, b) => b.startedAt - a.startedAt));

  type FlatEntry = {
    record: PerQuestionRecord;
    question: Question | null;
    sessionStartedAt: number;
  };
  const flat = $derived.by<FlatEntry[]>(() => {
    if (!$bank) return [];
    const byId = new Map($bank.questions.map((q) => [q.id, q]));
    const latest = new Map<string, FlatEntry>();
    for (const s of sessionsDesc) {
      for (const p of s.perQuestion) {
        if (!latest.has(p.id)) {
          latest.set(p.id, { record: p, question: byId.get(p.id) ?? null, sessionStartedAt: s.startedAt });
        }
      }
    }
    return [...latest.values()];
  });

  type SortKey = 'date' | 'section' | 'difficulty' | 'status' | 'domain' | 'skill';
  let sortKey = $state<SortKey>('date');

  const flatSorted = $derived.by<FlatEntry[]>(() => {
    const arr = flat.slice();
    const statusRank = (p: PerQuestionRecord) =>
      p.firstCorrect ? 0 : p.correctedOnRetry ? 1 : 2;
    arr.sort((a, b) => {
      switch (sortKey) {
        case 'date': return b.sessionStartedAt - a.sessionStartedAt;
        case 'section': return (a.question?.section ?? '').localeCompare(b.question?.section ?? '');
        case 'difficulty': return (a.question?.difficulty ?? '').localeCompare(b.question?.difficulty ?? '');
        case 'status': return statusRank(a.record) - statusRank(b.record);
        case 'domain': return (a.question?.domain ?? '').localeCompare(b.question?.domain ?? '');
        case 'skill': return (a.question?.skill ?? '').localeCompare(b.question?.skill ?? '');
      }
    });
    return arr;
  });

  function fmtDate(ms: number): string {
    return new Date(ms).toISOString().slice(0, 16).replace('T', ' ');
  }
  function fmtDur(start: number, end: number): string {
    const total = Math.round((end - start) / 1000);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  }
  function statusLabel(p: PerQuestionRecord): string {
    if (p.firstCorrect) return '✓ first try';
    if (p.correctedOnRetry) return '✗ → ✓ on retry';
    return '✗ wrong';
  }

  function buildGradedFromRecord(rec: SessionRecord) {
    if (!$bank) return null;
    const byId = new Map($bank.questions.map((q) => [q.id, q]));
    const questions: Question[] = [];
    const perQuestion: PerQuestionState[] = [];
    for (const p of rec.perQuestion) {
      const q = byId.get(p.id);
      if (!q) continue;
      questions.push(q);
      perQuestion.push({
        markedForReview: p.markedForReview,
        crossedOut: [],
        timeSpentMs: p.timeSpentMs,
        selectedChoice: q.type === 'mcq' && p.firstAnswer ? (p.firstAnswer as 'A'|'B'|'C'|'D') : undefined,
        sprInput: q.type === 'spr' && typeof p.firstAnswer === 'string' ? p.firstAnswer : undefined,
      });
    }
    const session: SessionState = {
      questions, perQuestion, currentIndex: 0,
      startedAt: rec.startedAt,
      timeLimitMs: rec.setup.timeLimitMin == null ? null : rec.setup.timeLimitMin * 60_000,
      endedAt: rec.endedAt,
    };
    return gradeSession(session);
  }

  function backToSetup() { screen.set('setup'); }

  function doResetDone() {
    if (!$currentUser) return;
    if (!confirm(`Clear all already-done question IDs for ${$currentUser}? This does not delete session history.`)) return;
    resetDone();
  }
  function doClearHistory() {
    if (!$currentUser) return;
    if (!confirm(`Delete all session history for ${$currentUser}? This cannot be undone.`)) return;
    clearHistory();
    history = [];
  }
  function doDeleteProfile() {
    if (!$currentUser) return;
    if (!confirm(`Permanently delete user ${$currentUser} and all their data? This cannot be undone.`)) return;
    deleteUser($currentUser);
    currentUser.set(null);
  }
  function switchUser() {
    localStorage.removeItem('satquiz.activeUser');
    currentUser.set(null);
  }

  function explanationAction(node: HTMLElement, html: string) {
    function set(h: string) { node.innerHTML = sanitize(h); renderMathIn(node); }
    set(html);
    return { update: set };
  }
</script>

<main class="history">
  <header class="top">
    <button class="link" onclick={backToSetup}>← Back to setup</button>
    <h1>History — {$currentUser}</h1>
  </header>

  <div class="tabs" role="tablist">
    <button role="tab" aria-selected={tab === 'sessions'} class:active={tab === 'sessions'} onclick={() => (tab = 'sessions')}>Sessions</button>
    <button role="tab" aria-selected={tab === 'all'} class:active={tab === 'all'} onclick={() => (tab = 'all')}>All questions</button>
  </div>

  {#if tab === 'sessions'}
    {#if sessionsDesc.length === 0}
      <p class="empty">No sessions yet.</p>
    {:else}
      <table class="sessions">
        <thead>
          <tr><th></th><th>Date</th><th>Section</th><th>Score</th><th>Drilled</th><th>Duration</th></tr>
        </thead>
        <tbody>
          {#each sessionsDesc as s, i}
            {@const drilled = s.perQuestion.filter((p) => p.correctedOnRetry).length}
            <tr onclick={() => (expandedSession = expandedSession === i ? null : i)}>
              <td class="caret">{expandedSession === i ? '▾' : '▸'}</td>
              <td>{fmtDate(s.startedAt)}</td>
              <td>{s.setup.section === 'math' ? 'Math' : 'R&W'}</td>
              <td>{s.score}/{s.perQuestion.length}</td>
              <td>{drilled > 0 ? `+${drilled}` : ''}</td>
              <td>{fmtDur(s.startedAt, s.endedAt)}</td>
            </tr>
            {#if expandedSession === i}
              {@const g = buildGradedFromRecord(s)}
              <tr class="detail">
                <td colspan="6">
                  {#if g}
                    <SessionResultTable graded={g} drillEnabled={false} />
                  {:else}
                    <p class="empty">Questions for this session are not in the current bank.</p>
                  {/if}
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    {/if}
  {:else}
    <div class="sortbar">
      Sort by:
      <select bind:value={sortKey}>
        <option value="date">Date (newest)</option>
        <option value="section">Section</option>
        <option value="difficulty">Difficulty</option>
        <option value="status">Status</option>
        <option value="domain">Domain</option>
        <option value="skill">Skill</option>
      </select>
    </div>
    {#if flatSorted.length === 0}
      <p class="empty">No questions yet.</p>
    {:else}
      <table class="all-q">
        <thead>
          <tr><th></th><th>Date</th><th>Section</th><th>Difficulty</th><th>Domain / Skill</th><th>Status</th></tr>
        </thead>
        <tbody>
          {#each flatSorted as e}
            {@const q = e.question}
            <tr onclick={() => (expandedQuestion = expandedQuestion === e.record.id ? null : e.record.id)}>
              <td class="caret">{expandedQuestion === e.record.id ? '▾' : '▸'}</td>
              <td>{fmtDate(e.sessionStartedAt)}</td>
              <td>{q ? (q.section === 'math' ? 'Math' : 'R&W') : '?'}</td>
              <td>{q?.difficulty ?? '?'}</td>
              <td>{q ? `${q.domain} — ${q.skill}` : ''}</td>
              <td>{statusLabel(e.record)}</td>
            </tr>
            {#if expandedQuestion === e.record.id}
              <tr class="detail">
                <td colspan="6">
                  {#if q}
                    <QuestionView
                      question={q}
                      pq={{
                        markedForReview: e.record.markedForReview,
                        crossedOut: [],
                        timeSpentMs: e.record.timeSpentMs,
                        selectedChoice: q.type === 'mcq' && e.record.firstAnswer ? (e.record.firstAnswer as 'A'|'B'|'C'|'D') : undefined,
                        sprInput: q.type === 'spr' && typeof e.record.firstAnswer === 'string' ? e.record.firstAnswer : undefined,
                      }}
                      onUpdate={() => {}}
                      readOnly
                    />
                    <p class="meta">
                      Your answer: <strong>{e.record.firstAnswer ?? '—'}</strong>;
                      correct: <strong>{q.type === 'mcq' ? (q.correctChoice ?? '—') : (q.acceptedAnswers ?? []).join(' or ')}</strong>
                    </p>
                    {#if q.explanation}
                      <h4>Explanation</h4>
                      <div class="explain" use:explanationAction={q.explanation}></div>
                    {/if}
                  {:else}
                    <p class="empty">Question not in current bank.</p>
                  {/if}
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    {/if}
  {/if}

  <footer class="bottom">
    <button class="link" onclick={switchUser}>Switch user</button>
    <button class="ghost" onclick={doResetDone}>Reset done list</button>
    <button class="ghost" onclick={doClearHistory}>Clear history</button>
    <button class="danger" onclick={doDeleteProfile}>Delete profile</button>
  </footer>
</main>

<style>
  .history { max-width: 60rem; margin: 1rem auto; padding: 1rem; background: white; border-radius: 8px; }
  .top { display: flex; align-items: baseline; gap: 1rem; }
  .top h1 { margin: 0; }
  .link { background: transparent; border: 0; color: #1a73e8; padding: 0; cursor: pointer; }
  .tabs { display: flex; gap: 0.5rem; border-bottom: 1px solid #ddd; margin: 1rem 0; }
  .tabs button { background: transparent; border: 0; padding: 0.5rem 1rem; border-bottom: 2px solid transparent; }
  .tabs button.active { border-bottom-color: #1a73e8; color: #1a73e8; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #eee; }
  tbody tr { cursor: pointer; }
  tr.detail td { background: #fafafa; cursor: default; }
  .caret { width: 1.5rem; color: #888; user-select: none; }
  .sortbar { margin: 0.5rem 0; color: #555; }
  .sortbar select { margin-left: 0.5rem; }
  .empty { color: #888; padding: 1rem 0; }
  .meta { color: #555; margin: 0.5rem 0; }
  .explain { padding: 0.5rem 0; }
  .bottom { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; }
  .ghost { background: transparent; border: 1px solid #ccc; padding: 0.4rem 0.75rem; border-radius: 4px; }
  .danger { background: transparent; border: 1px solid #b32400; color: #b32400; padding: 0.4rem 0.75rem; border-radius: 4px; }

  @media (max-width: 768px) {
    .history { margin: 0.5rem; padding: 0.75rem; }
    table { font-size: 0.85rem; }
    th, td { padding: 0.35rem 0.3rem; }
    .caret { width: 1rem; }
    .bottom { flex-direction: column; }
    .bottom button { width: 100%; }
  }
</style>
