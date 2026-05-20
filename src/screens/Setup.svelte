<script lang="ts">
  import { bank, screen, session } from '../lib/stores';
  import { loadSettings, saveSettings, loadDone, resetDone } from '../lib/storage';
  import { filterMatching, sampleQuestions } from '../lib/filter';
  import type { Difficulty, SessionState, SetupForm } from '../lib/types';

  let form: SetupForm = $state(loadSettings());
  let warning: string | null = $state(null);

  function toggleDiff(d: Difficulty) {
    form.difficulties = form.difficulties.includes(d)
      ? form.difficulties.filter((x) => x !== d)
      : [...form.difficulties, d];
  }

  function start() {
    if (!$bank) return;
    warning = null;
    if (form.difficulties.length === 0) {
      warning = 'Pick at least one difficulty.';
      return;
    }
    const done = loadDone();
    const pool = filterMatching($bank.questions, form, done);
    if (pool.length === 0) {
      warning = 'No matching unseen questions. Try widening filters or resetting your done list.';
      return;
    }
    const picked = sampleQuestions(pool, form.count);
    saveSettings(form);
    const state: SessionState = {
      questions: picked,
      perQuestion: picked.map(() => ({
        markedForReview: false, crossedOut: [], timeSpentMs: 0,
      })),
      currentIndex: 0,
      startedAt: Date.now(),
      timeLimitMs: (form.timeLimitMin ?? 15) * 60_000,
    };
    session.set(state);
    screen.set('session');
  }

  function doReset() {
    if (confirm('Clear your "already done" list?')) {
      resetDone();
      warning = 'Done list cleared.';
    }
  }
</script>

<main class="setup">
  <h1>SAT Practice</h1>

  <fieldset>
    <legend>Section</legend>
    <label><input type="radio" bind:group={form.section} value="math" /> Math</label>
    <label><input type="radio" bind:group={form.section} value="rw" /> Reading & Writing</label>
  </fieldset>

  <label class="row">
    Number of questions
    <input type="number" min="1" max="50" bind:value={form.count} />
  </label>

  <label class="row">
    Time limit (minutes)
    <input type="number" min="1" max="120" bind:value={form.timeLimitMin} />
  </label>

  <fieldset>
    <legend>Difficulty</legend>
    {#each ['E','M','H'] as d}
      <label class="chip">
        <input
          type="checkbox"
          checked={form.difficulties.includes(d as Difficulty)}
          onchange={() => toggleDiff(d as Difficulty)}
        />
        {d}
      </label>
    {/each}
  </fieldset>

  <label class="row">
    <input type="checkbox" bind:checked={form.excludeActive} />
    Exclude active (practice-test) questions
  </label>

  <div class="actions">
    <button class="primary" onclick={start} disabled={!$bank}>Start</button>
    <button class="ghost" onclick={doReset}>Reset done list</button>
  </div>

  {#if warning}<p class="warning">{warning}</p>{/if}
</main>

<style>
  .setup { max-width: 36rem; margin: 2rem auto; padding: 1.5rem;
    background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  fieldset { border: 1px solid #ddd; padding: 0.75rem; margin: 0.75rem 0; }
  .row { display: flex; align-items: center; gap: 0.75rem; margin: 0.5rem 0; }
  .row input[type="number"] { width: 6rem; }
  .chip { margin-right: 0.5rem; }
  .actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
  .primary { background: #1a73e8; color: white; border: 0; padding: 0.6rem 1.25rem; border-radius: 4px; }
  .primary:disabled { opacity: 0.5; }
  .ghost { background: transparent; border: 1px solid #ccc; padding: 0.6rem 1rem; border-radius: 4px; }
  .warning { color: #b32400; }

  @media (max-width: 768px) {
    .setup { margin: 0.5rem; padding: 1rem; border-radius: 6px; }
    .actions { flex-direction: column; }
    .actions button { width: 100%; }
  }
</style>
