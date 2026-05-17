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

  // Math questions in the real bank have an image figure that contains the
  // full prompt + four choices (equations can't be extracted as text). In that
  // case we show only the figure as the question body and present A/B/C/D as
  // empty selection buttons. R&W questions get the normal text rendering.
  const isMathFigureOnly = $derived(question.section === 'math' && !!question.figure);

  const figureSrc = $derived.by(() => {
    if (!question.figure) return '';
    const base = import.meta.env.BASE_URL;
    return base + question.figure.replace(/^\//, '');
  });

  let stimulusEl = $state<HTMLDivElement | undefined>(undefined);
  let promptEl = $state<HTMLDivElement | undefined>(undefined);

  $effect(() => {
    if (stimulusEl && question.stimulus) {
      stimulusEl.innerHTML = sanitize(question.stimulus);
      renderMathIn(stimulusEl);
    }
    if (promptEl && !isMathFigureOnly) {
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
    {#if isMathFigureOnly}
      <img class="figure full" src={figureSrc} alt="question" />
    {:else}
      <div class="prompt" bind:this={promptEl}></div>
      {#if question.figure}
        <img class="figure" src={figureSrc} alt="figure for question" />
      {/if}
    {/if}

    {#if question.type === 'mcq'}
      {#each (['A','B','C','D'] as Choice[]) as letter, i}
        <ChoiceButton
          {letter}
          html={isMathFigureOnly ? '' : (question.choices?.[i] ?? '')}
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
  .figure.full { max-width: 100%; max-height: 70vh; object-fit: contain; }

  @media (max-width: 768px) {
    .qv.split { grid-template-columns: 1fr; }
    .stimulus { max-height: 40vh; overflow-y: auto;
      padding: 0.5rem; border: 1px solid #eee; border-radius: 4px; background: #fafafa; }
    .figure.full { max-height: 55vh; }
  }
</style>
