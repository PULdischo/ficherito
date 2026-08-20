# Processing Documents

Learn how the processing pipeline works, and how to handle large collections efficiently.

---

## The Processing Pipeline

`ficherito process` runs these stages in sequence:

```
┌─────────────────┐
│  1. Scan        │  Find image files in dataset.images_dir
└────────┬────────┘  (rendering any PDFs to page images first)
         │
         ▼
┌─────────────────┐
│  2. Extract     │  HTR/OCR via the configured vision model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Entities    │  Extract people, places, dates (optional)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Build       │  Emit content, run Eleventy + Pagefind
└─────────────────┘
```

Translation is not part of `ficherito process` — run `ficherito translate`
separately (see [Translation](translation.md)).

---

## Running the Full Pipeline

```bash
ficherito process
```

Equivalent to:

```bash
ficherito extract
ficherito entities
ficherito build
```

### Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--limit` | `-l` | Limit number of documents | all |
| `--concurrency` | `-j` | Concurrent API requests | `10` |
| `--batch-size` | `-b` | Images per batch (memory) | `50` |
| `--skip-entities` | | Skip entity extraction | `False` |
| `--skip-build` | | Skip site building | `False` |
| `--verbose` | `-V` | Verbose output | `False` |

---

## Running Individual Stages

### Extract Text Only

```bash
ficherito extract
```

- Sends each image to the configured vision model for text extraction
- Saves results to `transcriptions/*.md`
- Already-transcribed images are skipped

### Extract Entities Only

```bash
ficherito entities
```

- Reads transcriptions from `transcriptions/`
- Saves results to `entities/*.json` plus `entities/consolidated.json`
- **Prerequisite:** run `ficherito extract` first

### Build Website Only

```bash
ficherito build
```

- Emits Markdown + frontmatter + images into `site/`
- Runs Eleventy and Pagefind
- **Prerequisite:** run `ficherito extract` first (entities are optional)

---

## Working with Large Collections

### Concurrency and Batching

Images are processed concurrently (`--concurrency`, default 10) and in
batches (`--batch-size`, default 50, to bound memory use while streaming
results to disk as each one completes).

```bash
# Faster, if your API tier allows it
ficherito process --concurrency 20

# More conservative, for rate-limited tiers
ficherito process --concurrency 3
```

```{warning}
Higher concurrency can hit API rate limits. Start conservative and increase gradually.
```

### Resuming Interrupted Processing

Both `extract` and `entities` skip files that already have output, so
re-running the same command after an interruption picks up where it left
off:

```bash
ficherito extract
# Skipped 340 images with existing transcriptions
# Extracting text (160/500)...
```

### Testing on a Subset

```bash
ficherito process --limit 20
```

---

## Handling Errors

Individual image failures are logged and skipped — processing continues
for the rest of the collection. Common cases:

**Rate limits** — the request is retried; if it persists, reduce `--concurrency`.

**Invalid images** — check the file is a valid, supported format (JPEG,
PNG, TIFF, WebP, HEIC, BMP, GIF, or PDF).

**Verbose output** for debugging:

```bash
ficherito process --verbose
```

---

## Checking Processing Status

```bash
ficherito status
```

```
                Ficherito Status
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Component      ┃ Status       ┃ Details        ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ Transcriptions │ 450 files    │ transcriptions │
│ Entities       │ 450 files    │ entities       │
│ Website        │ Built        │ site/_site     │
└────────────────┴──────────────┴────────────────┘
```

---

## Reprocessing Documents

### Reprocess Everything

```bash
rm -rf transcriptions/ entities/
ficherito process
```

### Reprocess a Specific Document

```bash
rm transcriptions/document_123.md entities/document_123.json
ficherito extract
ficherito entities
```

---

## Processing Different Document Types

Customize `prompts.text_extraction` in `ficherito.yaml` for the material:

```yaml
# Handwritten diaries
prompts:
  text_extraction: |
    This is a 19th-century American handwritten diary entry.
    The writer uses common abbreviations of the period...

# Printed documents
prompts:
  text_extraction: |
    This is a printed document from the early 20th century.
    Focus on preserving formatting and column structure...
```

For collections with very different document types, consider separate
Ficherito projects (each with its own `ficherito.yaml` and prompts) rather
than one shared configuration.

---

## Next Steps

- **[Transcription Details](transcription.md)** - Fine-tune text extraction
- **[Entity Extraction](entities.md)** - Customize entity recognition
- **[Building Sites](building-sites.md)** - Generate the website
