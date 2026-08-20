# Building Sites

Learn how to build and customize your document collection website.

---

## Architecture

Ficherito's website is an [Eleventy](https://www.11ty.dev/) (11ty) site with
[Pagefind](https://pagefind.app/) search and [Sveltia CMS](https://github.com/sveltia/sveltia-cms)
for in-browser content editing, living in a `site/` subdirectory of your project.

`ficherito build` does not render HTML itself. Instead it:

1. Creates `site/` from a bundled scaffold the first time it runs (if it doesn't already exist).
2. Emits each document as a Markdown file with frontmatter into `site/src/documents/`,
   copies compressed images into `site/src/assets/images/documents/`, and writes
   `site/src/_data/site.json` and `site/src/_data/allEntities.json`.
3. Runs `npm run build` inside `site/`, which runs Eleventy (rendering the pages)
   and then Pagefind (indexing them) via an `eleventy.after` build hook.

```bash
ficherito build
```

This creates a complete website in `site/_site/`.

---

## What Gets Built

```
site/
├── src/
│   ├── documents/           # one .md file per document (emitted by `build`)
│   ├── assets/
│   │   ├── css/style.css
│   │   └── images/documents/  # compressed document images (emitted by `build`)
│   ├── _data/
│   │   ├── site.json         # website config (emitted by `build`)
│   │   └── allEntities.json  # consolidated entities (emitted by `build`)
│   ├── index.njk              # password gate
│   ├── search.njk             # search page (-> main.html)
│   └── browse/
│       ├── dates.njk
│       └── entities.njk
├── admin/config.yml           # Sveltia CMS config
└── _site/                     # build output (index.html, main.html, documents/, browse/, pagefind/)
```

`site/src/documents/*.md`, `site/src/assets/images/documents/*`, and
`site/src/_data/*.json` are meant to be committed to git — that's how the
[GitHub Pages deployment](deployment.md#deploying-to-github-pages) and the
CMS work without re-running the Python pipeline in CI. `site/node_modules/`
and `site/_site/` are gitignored.

---

## Site Features

### Document Pages

Each document gets its own page at `/documents/<id>/` with:
- **Image viewer** - [OpenSeadragon](https://openseadragon.github.io/), zoomable
- **Transcription** - the extracted text, rendered from Markdown
- **Translation** (if enabled) - a tab alongside the original transcription
- **Entities** - people, places, dates found in the document
- **Previous/next navigation** - chronological, based on the document's date

### Full-Text Search

- Powered by [Pagefind](https://pagefind.app/), fully client-side
- Loaded off the critical rendering path (see [Search Performance](#search-performance) below)
- Highlights matching text when you click through to a document

### Browse by Date / Browse by Entity

Both pages are built from the emitted document content directly (no separate
data files to keep in sync) and support client-side filtering.

---

## Previewing Your Site

```bash
ficherito build
ficherito serve
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

For live-reloading while editing templates or CSS directly, use Eleventy's
own dev server instead:

```bash
cd site
npm start   # eleventy --serve, rebuilds on change
```

---

## Customizing the Site

### Site Title, Colors, and Password

```yaml
# ficherito.yaml
website:
  title: "Smith Family Papers"
  emoji: "📜"
  background_color: "#2d3748"
  accent_color: "#4a5568"
  password: "research2024"
```

These are written to `site/src/_data/site.json` on every `ficherito build` and
read by the Nunjucks templates. Editing that file by hand will be overwritten
on the next build — change `ficherito.yaml` instead.

```{note}
The password gate is client-side (`sessionStorage`), suitable for sharing
with collaborators, not for protecting sensitive materials.
```

### Editing Templates and CSS

Everything under `site/src/_includes/`, `site/src/assets/css/style.css`, and
the top-level `.njk` files is yours to edit directly and commit — `ficherito
build` never touches them (only `site/src/documents/`, `site/src/assets/images/documents/`,
and `site/src/_data/*.json` are regenerated).

### Show/Hide Sections

```yaml
website:
  enable_search: true
  enable_browse_dates: true
  enable_browse_entities: false
```

---

## Rebuilding After Changes

```bash
ficherito build
```

Re-run this after editing transcriptions, entities, or `ficherito.yaml`. It
re-emits all document content, so it's safe to run repeatedly.

### Full Rebuild

```bash
rm -rf site/_site
ficherito build
```

---

## Search Performance

Pagefind's UI bundle is loaded off the critical path on the search page
(`main.html`): a lightweight plain `<input>` is shown immediately, and the
real `pagefind-ui.js` bundle is injected via `requestIdleCallback` (falling
back to a short `setTimeout`) so the page never blocks on it. If you start
typing before it's ready, the load happens immediately on focus/input
instead, and your query is carried over once the real search box mounts.

If search still feels slow for a very large collection, the index itself
(under `site/_site/pagefind/`) is the next thing to look at — Pagefind
chunks it and only fetches what's needed per query, so size mostly affects
first-query latency, not page load.

---

## Editing Content via the CMS

Instead of editing `site/src/documents/*.md` by hand, collaborators can use
the Sveltia CMS at `/admin/` once the site is deployed. See
[Deployment](deployment.md#editing-content-with-sveltia-cms).

---

## Troubleshooting

### Site Won't Build

**Error:** `npm not found; skipping Eleventy/Pagefind build`

Install [Node.js](https://nodejs.org/) (20+ recommended), then re-run `ficherito build`.

### Search Not Working

Check that Pagefind's output exists:

```bash
ls site/_site/pagefind/
```

If missing, rebuild:

```bash
ficherito build
```

### Images Not Showing

Check that images are being found for compression — `ficherito build` looks
in `images/` and `data/images/` for `<document-id>.{jpg,jpeg,png,tiff,webp}`:

```bash
ls site/src/assets/images/documents/
```

---

## Next Steps

- **[Deployment](deployment.md)** - Put your site on the web with GitHub Pages
- **[Troubleshooting](../help/troubleshooting.md)** - Solve common problems
- **[Command Reference](../commands/build.md)** - Full build options
