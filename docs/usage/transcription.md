# Transcription

Learn how Ficherito extracts and cleans text from historical document images.

---

## How Transcription Works

Ficherito sends each image to a vision-language model (via any
OpenAI-compatible endpoint — DashScope/Qwen-VL by default) with the
`text_extraction` prompt from `ficherito.yaml`, which both reads the
handwriting and cleans up the output in one pass.

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐
│ Document     │ ──▶ │ Vision-language     │ ──▶ │ Markdown +   │
│ Image        │     │ model reads + cleans│     │ frontmatter  │
└──────────────┘     └────────────────────┘     └──────────────┘
```

---

## Understanding the Output

Each transcribed document produces a Markdown file with YAML frontmatter:

**File**: `transcriptions/1863-04-15_page_001.md`

```markdown
---
title: 1863-04-15_page_001
extracted_at: '2026-01-15T14:32:00Z'
model: qwen-vl-max
confidence: 0.92
---

April 15th 1863

Dear Sarah,

I write to you from camp near Fredericksburg...
```

| Frontmatter field | Description |
|--------------------|-------------|
| `title` | The document ID (image filename stem) |
| `extracted_at` | Timestamp of processing |
| `model` | Model used |
| `confidence` | Model's confidence score, if reported (0-1) |

The document's date isn't stored here — it's derived from the filename
(via `undate`) when the site is built, not written into the transcription
file.

---

## Customizing the Transcription Prompt

The default `prompts.text_extraction` in `ficherito.yaml` works well for
most English historical documents. Customize it for different languages,
time periods, handwriting styles, or specialized content — the `{raw_text}`
placeholder is where the raw OCR pass gets inserted for cleanup:

### Example: 18th Century Documents

```yaml
prompts:
  text_extraction: |
    You are transcribing an 18th-century handwritten document.

    Important conventions of this period:
    - The letter 's' often looks like 'f' (the "long s")
    - Abbreviations are common (e.g., "ye" for "the", "wch" for "which")
    - Spelling was not standardized

    Guidelines:
    1. Preserve original spelling exactly
    2. Expand the long 's' to regular 's'
    3. Keep abbreviations as written, noting expansion in [brackets]
    4. Mark illegible text with [?] or [illegible]

    Raw OCR text:
    {raw_text}

    Cleaned transcription:
```

### Example: Non-English Documents

```yaml
prompts:
  text_extraction: |
    You are transcribing a 19th-century German handwritten letter.
    The text uses Kurrent script (old German handwriting).

    Guidelines:
    1. Transcribe into modern German characters
    2. Preserve original spelling and grammar
    3. Keep ß, ü, ö, ä as written
    4. Mark unclear text with [?]

    Raw OCR text:
    {raw_text}

    Saubere Transkription:
```

### Example: Legal Documents

```yaml
prompts:
  text_extraction: |
    You are transcribing a historical legal document (deed, will, or court record).

    Pay special attention to:
    - Proper names (parties, witnesses, officials)
    - Dates and places
    - Monetary amounts and property descriptions
    - Legal terminology (preserve exactly)

    Raw OCR text:
    {raw_text}

    Cleaned transcription:
```

---

## Editing Transcriptions

Transcriptions are plain Markdown, so correcting them is just editing text:

```bash
nano transcriptions/document_001.md
```

Edit the body below the frontmatter, save, and rebuild:

```bash
ficherito build
```

Or use the Sveltia CMS at `/admin/` once deployed — see
[Deployment](deployment.md#editing-content-with-sveltia-cms).

### Bulk Find/Replace

```bash
find transcriptions/ -name "*.md" -exec sed -i 's/tbe/the/g' {} \;
```

---

## Quality Control

### Review Low-Confidence Transcriptions

```bash
grep -L "confidence" transcriptions/*.md   # files with no confidence reported
grep -l "confidence: 0.[0-6]" transcriptions/*.md   # confidence below 0.7
```

### Spot-Check a Random Document

```bash
cat "$(ls transcriptions/*.md | shuf -n 1)"
```

---

## Next Steps

- **[Entity Extraction](entities.md)** - Extract people, places, and dates
- **[Building Sites](building-sites.md)** - Create your website
- **[HTR and OCR](../concepts/htr-ocr.md)** - How text extraction works under the hood
