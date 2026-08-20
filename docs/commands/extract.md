# ficherito extract

Extract text from document images using the configured vision-language model.

---

## Usage

```bash
ficherito extract [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--limit` | `-l` | Limit number of documents | all |
| `--concurrency` | `-j` | Concurrent API requests | `10` |

---

## What It Does

1. Scans `dataset.images_dir` for image files (rendering any PDFs to page images first)
2. Sends each image, concurrently, to the configured vision-language model
3. Cleans up the raw output using the `prompts.text_extraction` prompt
4. Saves each result as Markdown with YAML frontmatter to `transcriptions/`

```
images/
├── letter_001.jpg     → transcriptions/letter_001.md
├── letter_002.jpg     → transcriptions/letter_002.md
└── diary_page_001.jpg → transcriptions/diary_page_001.md
```

Images that already have a transcription file are skipped, so it's safe to
re-run after adding new images.

---

## Examples

### Extract All Images

```bash
ficherito extract
```

### Test on a Few Images

```bash
ficherito extract --limit 5
```

### Higher Concurrency

```bash
ficherito extract --concurrency 20
```

```{warning}
Higher concurrency can hit API rate limits faster. Increase gradually.
```

---

## Output Format

```markdown
---
title: letter_001
extracted_at: '2026-01-15T10:30:00Z'
model: qwen-vl-max
confidence: 0.94
---

Dear Brother,

I write to inform you of our safe arrival in Philadelphia...
```

---

## Configuration

```yaml
prompts:
  text_extraction: |
    Transcribe all handwritten and printed text in this image.

    Guidelines:
    - Preserve original spelling
    - Maintain paragraph structure
    - Note illegible sections as [illegible]
    - Expand common abbreviations in [brackets]
```

`.env`:

```bash
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=qwen-vl-max
```

---

## Handling Low Confidence

```bash
# List transcriptions with confidence below 0.7
grep -l "confidence: 0.[0-6]" transcriptions/*.md
```

Review the source image and correct the Markdown file directly, or refine
`prompts.text_extraction` and reprocess.

---

## Image Preparation Tips

| Property | Recommendation |
|----------|----------------|
| Resolution | 300+ DPI |
| Format | JPEG, PNG, TIFF, WebP, HEIC, or PDF |
| Color | Grayscale or color |
| Orientation | Upright, not rotated |

---

## See Also

- **[HTR and OCR](../concepts/htr-ocr.md)** - Understanding text extraction
- **[Processing Documents](../usage/processing-documents.md)** - Usage guide
- **[Configuration](../usage/configuration.md)** - Full configuration reference
