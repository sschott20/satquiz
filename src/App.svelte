<script lang="ts">
  import { onMount } from 'svelte';
  import { screen, bank, currentUser } from './lib/stores';
  import UserGate from './screens/UserGate.svelte';
  import Setup from './screens/Setup.svelte';
  import Session from './screens/Session.svelte';
  import Review from './screens/Review.svelte';
  import History from './screens/History.svelte';
  import type { QuestionBank } from './lib/types';

  let loadError: string | null = $state(null);

  onMount(async () => {
    try {
      const base = import.meta.env.BASE_URL;
      const res = await fetch(`${base}questions.json`);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = (await res.json()) as QuestionBank;
      bank.set(data);
    } catch (e) {
      loadError = e instanceof Error ? e.message : String(e);
    }
  });
</script>

{#if loadError}
  <main class="status">
    <h1>Could not load questions</h1>
    <p>{loadError}</p>
  </main>
{:else if $bank == null}
  <main class="status"><p>Loading…</p></main>
{:else if $currentUser == null}
  <UserGate />
{:else if $screen === 'setup'}
  <Setup />
{:else if $screen === 'session'}
  <Session />
{:else if $screen === 'review'}
  <Review />
{:else}
  <History />
{/if}

<style>
  .status { padding: 2rem; font-family: system-ui, sans-serif; }
</style>
