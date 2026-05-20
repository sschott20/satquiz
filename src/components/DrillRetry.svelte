<script lang="ts">
  import { matchesSpr } from '../lib/math';
  import type { Choice, Question } from '../lib/types';

  type Props = { question: Question; onResolve: () => void };
  let { question, onResolve }: Props = $props();

  let wrongPing = $state(false);
  let sprValue = $state('');

  function flashWrong() {
    wrongPing = true;
    setTimeout(() => { wrongPing = false; }, 350);
  }

  function pickMcq(c: Choice) {
    if (question.correctChoice === c) {
      onResolve();
    } else {
      flashWrong();
    }
  }

  function checkSpr() {
    if (matchesSpr(sprValue, question.acceptedAnswers ?? [])) {
      onResolve();
    } else {
      flashWrong();
    }
  }
</script>

<div class="drill" class:wrong={wrongPing}>
  <span class="label">Try again:</span>
  {#if question.type === 'mcq'}
    <div class="row">
      {#each (['A','B','C','D'] as Choice[]) as c}
        <button onclick={() => pickMcq(c)}>{c}</button>
      {/each}
    </div>
  {:else if question.type === 'spr'}
    <div class="row">
      <input
        type="text"
        inputmode="numeric"
        placeholder="Your answer"
        bind:value={sprValue}
        onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); checkSpr(); } }}
      />
      <button onclick={checkSpr}>Check</button>
    </div>
  {/if}
</div>

<style>
  .drill { padding: 0.5rem; margin: 0.5rem 0; border: 1px solid #ccc; border-radius: 4px; background: #fff; }
  .drill.wrong { animation: shake 0.35s ease; border-color: #b32400; }
  .label { font-size: 0.85rem; color: #555; margin-right: 0.5rem; }
  .row { display: inline-flex; gap: 0.4rem; align-items: center; }
  button { padding: 0.4rem 0.75rem; border: 1px solid #888; border-radius: 4px; background: white; min-width: 2.5rem; }
  input { padding: 0.4rem 0.5rem; border: 1px solid #888; border-radius: 4px; width: 10rem; }
  @keyframes shake {
    0%,100% { transform: translateX(0); }
    25% { transform: translateX(-4px); }
    75% { transform: translateX(4px); }
  }
</style>
