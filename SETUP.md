# Kirubel GitHub Profile

This repository is the special public profile repository for [`@kirawebdesigner`](https://github.com/kirawebdesigner). The README is designed around four featured builds, two self-hosted radars, a public activity summary, and one coherent green accent.

## Local regeneration

The dynamic SVGs are generated with Python’s standard library and GitHub’s public REST API:

```bash
python scripts/generate_profile.py \
  --user kirawebdesigner \
  --data assets/skills.json \
  --projects assets/projects.json \
  --out assets
```

The generator refreshes the self-rated radar, interactive skill graphs, public language radar, project cards, profile snapshot, and recent public activity chart. The README uses a dark-first red accent system, a short mobile-safe live typing intro, and a Komarev visitor-count badge in the hero. The README’s featured-projects showcase uses authentic, self-hosted preview images copied from `kiraweb.pro.et/assets/projects/` into `assets/portfolio/`; each featured image is a direct link to a live product, portfolio case study, or verified GitHub repository. The showcase is aligned with the portfolio’s actual project set rather than a generic project template. It excludes forked repositories and excludes HTML, CSS, and build/configuration languages from the language radar so the result better reflects application code. The README uses a short third-party typing animation with deliberately short lines and a constrained width so it remains readable on narrow mobile screens.

## GitHub Actions

`.github/workflows/refresh.yml` runs daily at 03:30 UTC and can also be started manually from the Actions tab. It uses the built-in `GITHUB_TOKEN` and requests only `contents: write`, which is required to commit regenerated SVGs to this repository. No personal access token or repository secret is required for this workflow.

## Optional portrait

No photo was included in the supplied materials, so the README intentionally does not show a portrait. If a suitable image is added locally, `scripts/dotify.py` can generate `assets/portrait.svg`; the portrait can then be linked from the README after reviewing its crop and size on mobile.

## GitHub settings

Keep the repository public so the profile README and its self-hosted images are visible to visitors. If the scheduled workflow cannot push, open **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions**. The generated assets should be reviewed in both GitHub themes after the first manual run.
