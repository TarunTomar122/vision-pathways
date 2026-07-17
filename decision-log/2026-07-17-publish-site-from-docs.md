# Publish Research Site From `docs/`

## Intended Commit Subject

`Publish research site from docs`

## Problem Or Decision

GitHub Pages can publish a static site directly from the `/docs` directory on the `main` branch. The repository previously stored research protocols in `docs/` and the website in `site/`, so the website could not use that simple deployment mode without moving one of those collections.

## Files And Behavior Changed

- Moved the static research website from `site/` to `docs/` and added `docs/.nojekyll` so GitHub Pages serves the generated assets without Jekyll processing.
- Moved research protocols and status documents from `docs/` to `research-docs/`.
- Updated `README.md`, `paper/submission-checklist.md`, and `research-docs/current_status.md` to use the new paths.
- Updated `scripts/generate_paper_assets.py` to write website assets into `docs/assets/`.
- Updated `scripts/verify_submission.py` to validate the Pages site and the relocated research documents.
- Made generated PDF and SVG metadata deterministic so running the submission verifier repeatedly does not create timestamp or randomized-ID changes.

## Alternatives Considered

- Keep the site in `site/` and deploy it through a custom GitHub Actions workflow. This adds deployment configuration without improving the static site.
- Publish from a separate `gh-pages` branch. This would introduce another branch and synchronization step.
- Duplicate the website under both `site/` and `docs/`. This risks the two copies diverging.

The branch `/docs` deployment was selected because it is the smallest maintainable setup and keeps one canonical website copy.

## Verification Evidence

- `make PYTHON=/tmp/vlm-paper-venv/bin/python submission`
- `python3 -m py_compile scripts/generate_paper_assets.py scripts/verify_submission.py`
- `git --git-dir=.git-data --work-tree=. diff --check`
- Ran the complete submission target twice and confirmed the binary diff SHA-256 remained `97c2c8059e6680258d5d71f075f2651aa7552b98a4c57c713311fa9df287e8e6`.
- Rendered `docs/index.html` with Chromium at 1440 x 1000 and visually inspected the result.

## Known Limitations And Unsupported Claims

- GitHub Pages must still be enabled in repository settings with source `main` and folder `/docs`.
- The site does not configure a custom domain.
- Repository links embedded in the page still use the current GitHub repository name. GitHub normally redirects after a rename, but the links should be updated once the final name is chosen.
- This packaging change does not alter or strengthen any experimental result.

## Next Action Enabled

Enable GitHub Pages from `main` and `/docs`, then verify the public URL after GitHub completes its deployment.
