# ficherito serve

Serve the built site locally for preview, using Python's built-in HTTP server.

---

## Usage

```bash
ficherito serve [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--port` | `-p` | Port number | `8000` |
| `--host` | `-h` | Host address | `localhost` |

---

## What It Does

Serves the directory at `output.site_dir` (`site/_site` by default) as
static files. It does **not** rebuild or watch for changes — re-run
`ficherito build` after editing content, then `serve` will pick up the new
output on the next request.

```bash
ficherito serve
```

```
Serving at http://localhost:8000
Press Ctrl+C to stop.
```

If `site/_site` doesn't exist yet, `serve` exits with an error telling you
to run `ficherito build` first.

---

## Examples

### Custom Port

```bash
ficherito serve --port 3000
```

### Network Access

```bash
ficherito serve --host 0.0.0.0
```

Makes the server reachable from other devices on your local network at
`http://<your-ip>:<port>`.

---

## Development Workflow

For live-reloading while editing Eleventy templates or CSS directly, use
Eleventy's own dev server instead, which rebuilds on save:

```bash
cd site
npm start   # eleventy --serve
```

Use `ficherito serve` for a quick preview after `ficherito build`; use
`npm start` inside `site/` when actively editing templates.

---

## Troubleshooting

### Site Directory Not Found

```
Error: Site directory not found: site/_site
Run 'ficherito build' first.
```

Run `ficherito build`, then `ficherito serve`.

### Port Already in Use

```bash
ficherito serve --port 8001
```

---

## See Also

- **[build](build.md)** - Generate the site
- **[deploy](deploy.md)** - Deploy to Netlify
- **[Building Sites](../usage/building-sites.md)** - Usage guide
