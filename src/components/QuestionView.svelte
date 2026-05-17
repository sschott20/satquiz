<script lang="ts">
  import { sanitize, renderMathIn } from '../lib/sanitize';
  import ChoiceButton from './ChoiceButton.svelte';
  import SprInput from './SprInput.svelte';
  import type { Choice, PerQuestionState, Question } from '../lib/types';

  type Props = {
    question: Question;
    pq: PerQuestionState;
    onUpdate: (patch: Partial<PerQuestionState>) => void;
    readOnly?: boolean;
  };
  let { question, pq, onUpdate, readOnly = false }: Props = $props();

  let stimulusEl = $state<HTMLDivElement | undefined>(undefined);
  let promptEl = $state<HTMLDivElement | undefined>(undefined);

  $effect(() => {
    if (stimulusEl && question.stimulus) {
      stimulusEl.innerHTML = sanitize(question.stimulus);
      renderMathIn(stimulusEl);
    }
    if (promptEl) {
      promptEl.innerHTML = sanitize(question.prompt);
      renderMathIn(promptEl);
    }
  });

  function pick(c: Choice) {
    if (!readOnly) onUpdate({ selectedChoice: c });
  }
  function toggleCross(c: Choice) {
    if (readOnly) return;
    const has = pq.crossedOut.includes(c);
    onUpdate({
      crossedOut: has ? pq.crossedOut.filter((x) => x !== c) : [...pq.crossedOut, c],
    });
  }
</script>

<div class="qv" class:split={!!question.stimulus && question.section === 'rw'}>
  {#if question.stimulus}
    <div class="stimulus" bind:this={stimulusEl}></div>
  {/if}

  <div class="qbody">
    <div class="prompt" bind:this={promptEl}></div>
    {#if question.figure}
      <img class="figure" src={question.figure} alt="figure for question" />
    {/if}

    {#if question.type === 'mcq' && question.choices}
      {#each (['A','B','C','D'] as Choice[]) as letter, i}
        <ChoiceButton
          {letter}
          html={question.choices[i]}
          selected={pq.selectedChoice === letter}
          crossedOut={pq.crossedOut.includes(letter)}
          onSelect={() => pick(letter)}
          onToggleCross={() => toggleCross(letter)}
        />
      {/each}
    {:else if question.type === 'spr'}
      <SprInput
        value={pq.sprInput}
        onChange={(v) => !readOnly && onUpdate({ sprInput: v })}
      />
    {/if}
  </div>
</div>

<style>
  .qv { display: grid; gap: 1rem; }
  .qv.split { grid-template-columns: 1fr 1fr; }
  .stimulus, .prompt { line-height: 1.6; }
  .figure { max-width: 100%; height: auto; margin: 0.5rem 0; }
</style>
