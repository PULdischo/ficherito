# ficherito process

Run the extract → entities → build pipeline on your document collection.

---

## Usage

```bash
ficherito process [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--limit` | `-l` | Limit number of documents to process | all |
| `--concurrency` | `-j` | Concurrent API requests | `10` |
| `--batch-size` | `-b` | Images per batch (memory efficiency) | `50` |
| `--skip-entities` | | Skip entity extraction | `False` |
| `--skip-build` | | Skip site building | `False` |
| `--verbose` | `-V` | Verbose output, including tracebacks on error | `False` |

---

## Pipeline Steps

```
1. EXTRACT   → Text extraction via the configured vision-language model
2. ENTITIES  → Named entity extraction (unless --skip-entities)
3. BUILD     → Emit content, run Eleventy + Pagefind (unless --skip-build)
```

Translation is **not** included — run `ficherito translate` separately, then
`ficherito build` again if you want translated text on the site.

---

## Examples

### Run Full Pipeline

```bash
ficherito process
```

### Test on a Subset

```bash
ficherito process --limit 20
```

### Skip Entities and Build (transcription only)

```bash
ficherito process --skip-entities --skip-build
```

### Higher Throughput

```bash
ficherito process --concurrency 20 --batch-size 100
```

---

## Progress Output

```
⠋ Scanning images...
⠋ Extracting text (120/500)...
⠋ Extracting entities (450/500)...
⠋ Building website...

✓ Pipeline complete!
  Transcriptions: transcriptions/
  Entities: entities/
  Website: site/_site/
```

---

## Resuming Interrupted Runs

`extract` and `entities` each skip files with existing output, so just
re-run the same command:

```bash
ficherito process
```

---

## Output Files

```
project/
├── transcriptions/
│   ├── image_001.md
│   └── ...
├── entities/
│   ├── image_001.json
│   └── consolidated.json
└── site/
    ├── src/documents/
    └── _site/
```

---

## Error Handling

Individual image failures are logged and don't stop the run. For full
tracebacks on failure:

```bash
ficherito process --verbose
```

---

## See Also

- **[extract](extract.md)** - Text extraction details
- **[entities](entities.md)** - Entity extraction details
- **[build](build.md)** - Site build details
- **[Configuration Guide](../usage/configuration.md)** - Full configuration reference
