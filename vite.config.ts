import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

const base = process.env.BASE ?? '/';

export default defineConfig({
  base,
  plugins: [svelte()],
  resolve: {
    conditions: process.env.VITEST ? ['browser'] : [],
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/unit/**/*.test.ts', 'tests/components/**/*.test.ts'],
  },
});
