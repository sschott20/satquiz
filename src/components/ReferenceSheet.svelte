<script lang="ts">
  type Props = { onClose: () => void };
  let { onClose }: Props = $props();
  const base = import.meta.env.BASE_URL;
</script>

<div class="backdrop" onclick={onClose} role="presentation"></div>
<div class="panel" role="dialog" aria-label="Reference sheet">
  <header>
    <h3>Reference</h3>
    <button onclick={onClose}>Close</button>
  </header>
  <img src="{base}reference-sheet.svg" alt="SAT math reference sheet" />
</div>

<style>
  .backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.2); }
  .panel { position: fixed; top: 4rem; right: 2rem; width: 28rem; background: white;
    border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 1rem;
    max-height: 80vh; overflow-y: auto; z-index: 10; }
  header { display: flex; justify-content: space-between; align-items: center; }
  img { width: 100%; height: auto; }

  @media (max-width: 768px) {
    .panel { top: 2rem; right: 0.5rem; left: 0.5rem; width: auto; padding: 0.75rem; }
  }
</style>
