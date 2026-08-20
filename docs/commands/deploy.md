# ficherito deploy

Deploy the built site to Netlify using `netlify-python`.

```{note}
This command only supports Netlify. For GitHub Pages, there's no CLI
command — you build locally, commit `site/`, and push; a GitHub Actions
workflow handles the rest. See [Deployment](../usage/deployment.md#deploying-to-github-pages).
```

---

## Usage

```bash
ficherito deploy [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--prod` / `--draft` | | Deploy to production or a draft preview | `--prod` |
| `--site` | `-s` | Netlify site ID | `website.netlify_site_id` in config, or `NETLIFY_SITE_ID` env var |
| `--build` / `--no-build` | | Build the site before deploying | `--build` |

---

## Requirements

```bash
pip install netlify-python
```

```bash
# .env
NETLIFY_TOKEN=your-token
```

Get a token from [app.netlify.com/user/applications](https://app.netlify.com/user/applications#personal-access-tokens).

---

## What It Does

1. Builds the site (unless `--no-build`)
2. Zips `output.site_dir` (`site/_site`)
3. Uploads it via the Netlify API as a production or draft deploy

---

## Examples

### Deploy to Production

```bash
ficherito deploy
```

### Draft Preview

```bash
ficherito deploy --draft
```

### Specify a Site ID

```bash
ficherito deploy --site your-site-id
```

First deploy to a given site ID creates it if it doesn't exist yet. Save
the ID afterward:

```yaml
# ficherito.yaml
website:
  netlify_site_id: "your-site-id"
```

### Skip the Build Step

Deploy the existing `site/_site/` without rebuilding:

```bash
ficherito deploy --no-build
```

---

## Troubleshooting

### "netlify-python not installed"

```bash
pip install netlify-python
```

### "NETLIFY_TOKEN not found"

Add it to `.env`, or export it:

```bash
export NETLIFY_TOKEN=your-token
```

### "No site ID provided"

Set `website.netlify_site_id` in `ficherito.yaml`, pass `--site`, or set `NETLIFY_SITE_ID`.

### "Site directory not found"

Run `ficherito build` first, or drop `--no-build`.

---

## See Also

- **[build](build.md)** - Generate the site
- **[serve](serve.md)** - Local preview
- **[Deployment Guide](../usage/deployment.md)** - GitHub Pages (recommended) and Netlify
