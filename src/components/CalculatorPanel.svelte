<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  type Props = { onClose: () => void };
  let { onClose }: Props = $props();

  let containerEl: HTMLDivElement | undefined = $state();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let calc: any = null;
  let failed = $state(false);

  onMount(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const Desmos = (window as any).Desmos;
    if (!Desmos || !containerEl) {
      failed = true;
      return;
    }
    calc = Desmos.GraphingCalculator(containerEl, { keypad: true });
  });

  onDestroy(() => { if (calc) calc.destroy(); });
</script>

<div class="panel" role="dialog" aria-label="Calculator">
  <header>
    <h3>Calculator</h3>
    <button onclick={onClose}>Close</button>
  </header>
  <div class="graph" bind:this={containerEl}></div>
  {#if failed}
    <p class="err">Desmos failed to load. Check your connection.</p>
  {/if}
</div>

<style>
  .panel { position: fixed; bottom: 4rem; right: 2rem; width: 32rem; height: 24rem;
    background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    display: flex; flex-direction: column; z-index: 10; }
  header { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1rem; border-bottom: 1px solid #eee; }
  .graph { flex: 1; }
  .err { padding: 1rem; color: #b32400; }

  @media (max-width: 768px) {
    .panel { bottom: 0.5rem; right: 0.5rem; left: 0.5rem; width: auto; height: 60vh; }
  }
</style>
