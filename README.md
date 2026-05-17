# SAT Practice

A personal SAT practice tool. Static site, runs on GitHub Pages.

## Local dev

```bash
npm install
npm run dev        # http://localhost:5173/
npm test           # unit + component tests
npm run test:e2e   # end-to-end smoke
npm run build      # produces dist/
```

## Deployment

Pushing to `main` builds and deploys via GitHub Actions. In repo settings,
set **Pages → Build and deployment → Source = GitHub Actions**.

The Vite base path is set from the `BASE` env var in CI to `/<repo-name>/`
so the app works under the GitHub Pages URL.

## Questions data

`public/questions.json` is the bundled question bank. The current copy is
hand-authored sample data; the real bank is produced by the parser under
`pipeline/` from the four PDFs in `source/`.
