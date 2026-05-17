<script lang="ts">
  type Props = { value: string | undefined; onChange: (v: string) => void };
  let { value, onChange }: Props = $props();
</script>

<input
  class="spr"
  type="text"
  inputmode="numeric"
  placeholder="Your answer"
  value={value ?? ''}
  oninput={(e) => onChange((e.target as HTMLInputElement).value)}
/>

<style>
  .spr { font-size: 1.1rem; padding: 0.5rem; border: 1px solid #888; border-radius: 4px; width: 12rem; }
</style>
