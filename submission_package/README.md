# VFL Project Submission Package

This folder is the **clean hand-in package** for the project. It contains the source code needed for the web demo and the Phase 3 research code.

## What is included

- `src/` — Next.js web application for the visualization/demo site
- `public/` — Static assets used by the web app
- `scripts/` — Helper scripts for development and deployment
- `vfl_base/phase3/src/` — Python source code for the Phase 3 VFL pipeline
- Project config files such as `package.json`, `next.config.ts`, `tsconfig.json`, and `vercel.json`

## What is not included

Do **not** submit local caches, large datasets, or generated checkpoints.

Examples of files that should stay out of the hand-in:

- `.next/`
- `node_modules/`
- `data/`
- `checkpoint_epoch_*.json`
- log files, export artifacts, and temporary outputs

## Demo link

**Production demo URL:** `https://<your-deployed-demo-link>`

Replace the placeholder with the public URL after deploying the web app to Vercel or another hosting platform.

## How to run locally

### Web demo

```bash
npm install
npm run dev
```

Then open:

```bash
http://localhost:3000
```

### Phase 3 Python code

If you want to reproduce the Phase 3 pipeline, go to the Python source folder and run the main script from there:

```bash
cd vfl_base/phase3/src
python3 main_phase4_full_pipeline.py
```

## Quick hand-in checklist

- [ ] `submission_package/` contains the final source code
- [ ] Demo URL is filled in with the real deployed link
- [ ] No checkpoints, logs, or dataset archives are included
- [ ] The web app runs locally with `npm run dev`
- [ ] The repo is pushed to GitHub

## Notes

- The local URL (`http://localhost:3000`) works only on your machine.
- To let other people test the project, use the deployed production URL.
- The GitHub branch for the clean submission package is `submission-package`.

---

**Happy Coding! 🚀**
