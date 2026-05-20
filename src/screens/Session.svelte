<script lang="ts">
  import { screen, session, graded } from '../lib/stores';
  import { gradeSession } from '../lib/grade';
  import { addDone } from '../lib/profile';
  import QuestionView from '../components/QuestionView.svelte';
  import Timer from '../components/Timer.svelte';
  import NavigatorPopup from '../components/NavigatorPopup.svelte';
  import CalculatorPanel from '../components/CalculatorPanel.svelte';
  import ReferenceSheet from '../components/ReferenceSheet.svelte';
  import HighlightLayer from '../components/HighlightLayer.svelte';
  import type { PerQuestionState } from '../lib/types';

  let showNav = $state(false);
  let showCalc = $state(false);
  let showRef = $state(false);
  let hideTimer = $state(false);

  let lastShownAt = $state(Date.now());
  let stimulusContainer = $state<HTMLElement | undefined>(undefined);

  function bumpTime(prevIndex: number) {
    const s = $session;
    if (!s) return;
    const now = Date.now();
    const delta = now - lastShownAt;
    s.perQuestion[prevIndex].timeSpentMs += delta;
    lastShownAt = now;
    session.set(s);
  }

  function goTo(i: number) {
    const s = $session;
    if (!s) return;
    bumpTime(s.currentIndex);
    s.currentIndex = Math.max(0, Math.min(i, s.questions.length - 1));
    session.set(s);
    showNav = false;
  }

  function next() {
    const s = $session;
    if (s) goTo(s.currentIndex + 1);
  }
  function back() {
    const s = $session;
    if (s) goTo(s.currentIndex - 1);
  }
  function toggleMark() {
    const s = $session;
    if (!s) return;
    const i = s.currentIndex;
    s.perQuestion[i].markedForReview = !s.perQuestion[i].markedForReview;
    session.set(s);
  }

  function updateCurrent(patch: Partial<PerQuestionState>) {
    const s = $session;
    if (!s) return;
    const i = s.currentIndex;
    s.perQuestion[i] = { ...s.perQuestion[i], ...patch };
    session.set(s);
  }

  function endSession() {
    const s = $session;
    if (!s) return;
    bumpTime(s.currentIndex);
    s.endedAt = Date.now();
    const result = gradeSession(s);
    graded.set(result);
    addDone(s.questions.map((q) => q.id));
    session.set(s);
    screen.set('review');
  }

  function confirmEnd() {
    if (confirm('End the test and see your results?')) endSession();
  }

  function onExpire() {
    endSession();
  }
</script>

{#if $session}
  {@const i = $session.currentIndex}
  {@const q = $session.questions[i]}
  {@const pq = $session.perQuestion[i]}

  <div class="topbar">
    <span class="section">{q.section === 'math' ? 'Math' : 'Reading & Writing'}</span>
    <Timer
      startedAt={$session.startedAt}
      totalMs={$session.timeLimitMs ?? 0}
      hidden={hideTimer}
      {onExpire}
    />
    <button class="link" onclick={() => (hideTimer = !hideTimer)}>
      {hideTimer ? 'Show' : 'Hide'} timer
    </button>
    <button class="link" onclick={confirmEnd}>End test</button>
  </div>

  <main class="qarea">
    <div class="qhead">
      <span>Question {i + 1} of {$session.questions.length}</span>
      <button class="flag" class:on={pq.markedForReview} onclick={toggleMark}>
        ⚑ Mark for review
      </button>
    </div>

    {#if q.section === 'rw' && q.stimulus}
      <HighlightLayer containerEl={stimulusContainer ?? null} />
    {/if}

    <div bind:this={stimulusContainer}>
      <QuestionView question={q} {pq} onUpdate={updateCurrent} />
    </div>
  </main>

  <div class="bottombar">
    <div class="left">
      {#if q.section === 'math'}
        <button onclick={() => (showCalc = !showCalc)}>Calculator</button>
        <button onclick={() => (showRef = !showRef)}>Reference</button>
      {/if}
    </div>
    <button onclick={() => (showNav = true)}>Question {i + 1} ▾</button>
    <div class="right">
      <button onclick={back} disabled={i === 0}>Back</button>
      {#if i === $session.questions.length - 1}
        <button class="primary" onclick={confirmEnd}>Submit</button>
      {:else}
        <button class="primary" onclick={next}>Next</button>
      {/if}
    </div>
  </div>

  {#if showNav}
    <NavigatorPopup
      perQuestion={$session.perQuestion}
      currentIndex={i}
      onJump={goTo}
      onClose={() => (showNav = false)}
    />
  {/if}
  {#if showCalc && q.section === 'math'}
    <CalculatorPanel onClose={() => (showCalc = false)} />
  {/if}
  {#if showRef && q.section === 'math'}
    <ReferenceSheet onClose={() => (showRef = false)} />
  {/if}
{/if}

<style>
  .topbar { display: flex; align-items: center; gap: 1rem; padding: 0.5rem 1rem;
    background: white; border-bottom: 1px solid #ddd; }
  .section { font-weight: 600; flex: 1; }
  .link { background: transparent; border: 0; color: #1a73e8; }
  .qarea { max-width: 60rem; margin: 1rem auto; padding: 1rem; background: white; border-radius: 8px; }
  .qhead { display: flex; justify-content: space-between; margin-bottom: 0.75rem; color: #333; }
  .flag { background: transparent; border: 1px solid #ccc; padding: 0.25rem 0.5rem; border-radius: 4px; }
  .flag.on { background: #fff59d; border-color: #f9a825; }
  .bottombar { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem;
    background: white; border-top: 1px solid #ddd; position: sticky; bottom: 0; }
  .bottombar .left { display: flex; gap: 0.5rem; }
  .bottombar .right { margin-left: auto; display: flex; gap: 0.5rem; }
  .primary { background: #1a73e8; color: white; border: 0; padding: 0.5rem 1rem; border-radius: 4px; }

  @media (max-width: 768px) {
    .topbar { flex-wrap: wrap; gap: 0.5rem; padding: 0.5rem; font-size: 0.9rem; }
    .section { flex-basis: 100%; }
    .qarea { margin: 0.5rem; padding: 0.75rem; border-radius: 6px; }
    .qhead { flex-wrap: wrap; gap: 0.5rem; font-size: 0.95rem; }
    .bottombar { flex-wrap: wrap; padding: 0.5rem; gap: 0.4rem; }
    .bottombar .left, .bottombar .right { flex: 1 1 auto; }
    .bottombar button { padding: 0.5rem 0.6rem; }
  }
</style>
