# Site for "Open physics data: what license and attribution terms should it carry?"

Quarto website, built from the content repository
[det-lab/open-physics-data-terms](https://github.com/det-lab/open-physics-data-terms)
(its `main` branch; the latest release tag is used only for the citation's version label) and deployed to GitHub Pages. Nothing in this repo is
content; the contributions, catalog, and open questions live in the other one.

## How it builds

- `build_index.py` reads `contributions.yml`, `catalog/catalog.csv`, and
  `open-questions.md` from the content repo and writes `index.qmd`. It also
  copies the contribution PDFs into `contributions/` so links are relative.
- `_quarto.yml` uses `theme: none` and `style.css`: plain semantic HTML,
  serif reading column, sidenotes in the margin on wide screens.
- `.github/workflows/publish.yml` runs on every push to `main`, on manual
  dispatch (optionally with a tag), and on a `contributions-released`
  repository-dispatch event.

## Setup once

1. In this repo: Settings → Pages → Source: GitHub Actions.
2. Settings → Secrets and variables → Actions → Variables: add
   `ZENODO_DOI` once the first Zenodo release exists (e.g. `10.5281/zenodo.1234567`).
3. Push to `main`; the site appears at
   https://det-lab.github.io/open-physics-data-terms-site/.

## Building locally

```
pip install pyyaml
git clone https://github.com/det-lab/open-physics-data-terms ../open-physics-data-terms
quarto preview
```
