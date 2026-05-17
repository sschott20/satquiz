<script lang="ts">
  import { onMount, onDestroy } from 'svelte';

  type Props = {
    startedAt: number;
    totalMs: number;
    hidden?: boolean;
    onExpire: () => void;
  };
  let { startedAt, totalMs, hidden = false, onExpire }: Props = $props();

  let remaining = $state(0);
  let interval: ReturnType<typeof setInterval> | undefined;
  let fired = false;

  function tick() {
    const elapsed = Date.now() - startedAt;
    remaining = Math.max(0, totalMs - elapsed);
    if (remaining <= 0 && !fired) {
      fired = true;
      onExpire();
    }
  }

  onMount(() => {
    tick();
    interval = setInterval(tick, 250);
  });
  onDestroy(() => { if (interval) clearInterval(interval); });

  function fmt(ms: number): string {
    const total = Math.ceil(ms / 1000);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
</script>

<span class="timer" data-testid="timer">
  {hidden ? 'Time hidden' : fmt(remaining)}
</span>

<style>
  .timer { font-variant-numeric: tabular-nums; font-size: 1.1rem; font-weight: 600; }
</style>
