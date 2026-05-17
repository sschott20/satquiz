import DOMPurify from 'dompurify';
import katex from 'katex';

const ALLOWED_TAGS = ['p', 'em', 'strong', 'u', 'br', 'span', 'mark'];
const ALLOWED_ATTR = ['class'];

export function sanitize(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
  });
}

export function renderMathIn(root: HTMLElement): void {
  const nodes = root.querySelectorAll<HTMLSpanElement>('span.math');
  nodes.forEach((node) => {
    const tex = node.textContent ?? '';
    try {
      katex.render(tex, node, { throwOnError: false, displayMode: false });
    } catch {
      node.textContent = tex;
    }
  });
}
