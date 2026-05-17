import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

const base = process.env.BASE ?? '/';
const inTest = !!process.env.VITEST;

export default defineConfig({
  base,
  plugins: [svelte()],
  // Only override resolve conditions during tests so we get Svelte's client build
  // in jsdom; in production we let Vite use its defaults (which include 'browser').
  ...(inTest ? { resolve: { conditions: ['browser'] } } : {}),
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/unit/**/*.test.ts', 'tests/components/**/*.test.ts'],
    server: {
      deps: {
        inline: [/svelte/],
      },
    },
  },
});
