<script lang="ts">
  import { currentUser } from '../lib/stores';
  import { listUsers, setActiveUser, migrateLegacy, hasLegacyData, slugify } from '../lib/profile';

  let name = $state('');
  let users = $state(listUsers());
  let showMigrationNote = $state(hasLegacyData());

  function pick(u: string) {
    name = u;
  }

  function submit() {
    const trimmed = name.trim();
    if (!trimmed) return;
    if (!slugify(trimmed)) return;
    setActiveUser(trimmed);
    if (showMigrationNote) migrateLegacy(trimmed);
    currentUser.set(trimmed);
  }
</script>

<main class="gate">
  <h1>SAT Practice</h1>
  <p class="lead">What's your name?</p>

  <form onsubmit={(e) => { e.preventDefault(); submit(); }}>
    <input
      type="text"
      placeholder="e.g. Alex"
      bind:value={name}
      aria-label="username"
      autocomplete="off"
      maxlength="40"
    />
    <button class="primary" type="submit" disabled={!name.trim()}>Start</button>
  </form>

  {#if showMigrationNote}
    <p class="migration"><em>Existing progress on this device will be moved to this profile.</em></p>
  {/if}

  {#if users.length > 0}
    <p class="lead small">Or pick a saved profile:</p>
    <div class="chips">
      {#each users as u}
        <button class="chip" onclick={() => pick(u)}>{u}</button>
      {/each}
    </div>
  {/if}

  <p class="footnote">Tracks your already-done questions and past sessions on this device only.</p>
</main>

<style>
  .gate { max-width: 28rem; margin: 4rem auto; padding: 1.5rem;
    background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  h1 { margin-top: 0; }
  .lead { margin: 0.5rem 0; }
  .lead.small { margin-top: 1rem; color: #555; font-size: 0.9rem; }
  form { display: flex; gap: 0.5rem; margin: 0.5rem 0; }
  input { flex: 1; padding: 0.6rem; border: 1px solid #888; border-radius: 4px; font-size: 1rem; }
  .primary { background: #1a73e8; color: white; border: 0; padding: 0.6rem 1.25rem; border-radius: 4px; }
  .primary:disabled { opacity: 0.5; }
  .chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .chip { background: #f1f3f4; border: 1px solid #ccc; padding: 0.4rem 0.75rem; border-radius: 16px; }
  .migration { color: #555; font-size: 0.9rem; }
  .footnote { color: #888; font-size: 0.8rem; margin-top: 1.5rem; }

  @media (max-width: 768px) {
    .gate { margin: 1rem 0.5rem; padding: 1rem; }
  }
</style>
