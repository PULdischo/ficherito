# ficherito build

Emit content into an Eleventy site project and build it (Eleventy + Pagefind).

---

## Usage

```bash
ficherito build [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--output` | `-o` | Override the built site's output directory | `output.site_dir` (`site/_site`) |
| `--base-url` | | Path prefix the site is served under (e.g. `/my-repo/` for GitHub Pages project sites) | `/` |

---

## What It Does

1. **Scaffolds** `site/` from Ficherito's bundled Eleventy/Pagefind/Sveltia
   project template, if it doesn't already exist
2. **Loads** transcriptions, entities, and translations; sorts documents chronologically
3. **Emits** each document as Markdown + frontmatter into `site/src/documents/`,
   compresses and copies images into `site/src/assets/images/documents/`,
   and writes `site/src/_data/site.json` and `allEntities.json`
4. **Installs** Node dependencies (`npm install`) inside `site/`, if `node_modules/` is missing
5. **Runs** `npm run build`, which runs Eleventy (rendering pages) and then
   Pagefind (indexing them, via an `eleventy.after` build hook)

```
transcriptions/ ─┐
entities/       ─┼─→ build ─→ site/src/documents/, _data/*.json ─→ npm run build ─→ site/_site/
translations/   ─┘
```

---

## Examples

### Build the Site

```bash
ficherito build
```

### Custom Output Directory

```bash
ficherito build --output ./public
```

### Build for a GitHub Pages Project Site

```bash
ficherito build --base-url "/my-repo/"
```

Sets `PATH_PREFIX` for the Eleventy build so internal links and asset paths
resolve correctly under a subpath. Leave as `/` (the default) for a custom
domain or a `<user>.github.io` root site.

---

## Generated Site Structure

```
site/_site/
├── index.html              # Password gate
├── main.html                # Search page
├── documents/
│   ├── letter_001/
│   │   └── index.html
│   └── ...
├── browse/
│   ├── dates.html
│   └── entities.html
├── assets/
│   ├── css/style.css
│   └── images/documents/
└── pagefind/                # Search index
```

---

## Configuration

```yaml
website:
  title: "Smith Family Papers"
  emoji: "📜"
  background_color: "#2d3748"
  accent_color: "#4a5568"
  password: "changeme"
  enable_search: true
  enable_browse_dates: true
  enable_browse_entities: true
  default_sort: "date"

output:
  eleventy_dir: "site"        # where the Eleventy project lives
  site_dir: "site/_site"      # where the built site ends up
```

Editing `website.enable_search: false` sets `ENABLE_SEARCH=false` for the
Eleventy build, skipping the Pagefind indexing step entirely.

---

## Customizing the Site

Everything under `site/src/_includes/`, `site/src/assets/css/style.css`,
`site/admin/config.yml`, and the top-level `.njk` files is yours to edit
and commit — `ficherito build` only ever regenerates
`site/src/documents/*.md`, `site/src/assets/images/documents/*`, and
`site/src/_data/*.json`. See [Building Sites](../usage/building-sites.md).

---

## Troubleshooting

### `npm not found; skipping Eleventy/Pagefind build`

Install [Node.js](https://nodejs.org/) 20+ and re-run `ficherito build`.

### "No documents found" / empty site

Run `ficherito extract` first — `build` reads from `transcriptions/`.

### Search Not Working

```bash
ls site/_site/pagefind/
```

If missing, check `website.enable_search` is `true` and that `npm`/Node.js
are installed, then rebuild.

---

## See Also

- **[serve](serve.md)** - Preview site locally
- **[deploy](deploy.md)** - Deploy to Netlify
- **[Building Sites](../usage/building-sites.md)** - Usage guide
- **[Deployment](../usage/deployment.md)** - GitHub Pages + Sveltia CMS setup
