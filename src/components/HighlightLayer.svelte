<script lang="ts">
  type Props = { containerEl: HTMLElement | null };
  let { containerEl }: Props = $props();

  function highlight() {
    if (!containerEl) return;
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) return;
    const range = sel.getRangeAt(0);
    if (!containerEl.contains(range.commonAncestorContainer)) return;
    try {
      const mark = document.createElement('mark');
      range.surroundContents(mark);
      sel.removeAllRanges();
    } catch {
      // surroundContents fails on partial-node ranges; ignore in MVP.
    }
  }

  function clearAll() {
    if (!containerEl) return;
    const marks = containerEl.querySelectorAll('mark');
    marks.forEach((m) => {
      const parent = m.parentNode;
      if (!parent) return;
      while (m.firstChild) parent.insertBefore(m.firstChild, m);
      parent.removeChild(m);
    });
  }
</script>

<div class="bar">
  <button onclick={highlight}>Highlight</button>
  <button onclick={clearAll}>Clear highlights</button>
</div>

<style>
  .bar { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; }
  .bar button { font-size: 0.85rem; padding: 0.25rem 0.5rem; border: 1px solid #ccc; background: white; border-radius: 4px; }
</style>
