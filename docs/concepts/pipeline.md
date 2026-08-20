# The Processing Pipeline

Understand how Ficherito transforms document images into a searchable, editable website.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FICHERITO PIPELINE                            │
└─────────────────────────────────────────────────────────────────┘

     ┌─────────────┐
     │ Local Folder│
     │ of Images   │
     └──────┬──────┘
            │
            ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  1. EXTRACTION    │     │ • Read images (+ render PDFs)       │
│                   │ ──▶ │ • Send to vision-language model     │
│  ficherito extract│     │ • Clean and format transcriptions   │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  2. ENTITIES      │     │ • Analyze transcriptions             │
│                   │ ──▶ │ • Identify people, places, dates    │
│ ficherito entities│     │ • Add contextual descriptions       │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  3. TRANSLATE     │     │ • Translate to target language      │
│  (optional, run   │ ──▶ │ • Save translated text              │
│  separately)      │     │ • Support multiple source languages │
│ ficherito translate│    │                                     │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  4. BUILD         │     │ • Emit Markdown + frontmatter        │
│                   │ ──▶ │ • Run Eleventy + Pagefind           │
│  ficherito build  │     │ • Output static, editable website   │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
     ┌─────────────┐
     │   Static    │
     │   Website   │
     └─────────────┘
```

`ficherito process` runs stages 1, 2, and 4 (translation is opt-in and run
separately, before rebuilding, so translated text is included).

---

## Stage 1: Extraction

**Purpose:** Convert document images to text.

**Input:** Images in `dataset.images_dir` (PDFs rendered to page images first)
**Output:** Markdown files with YAML frontmatter in `transcriptions/`

### Process

1. **Scan** the configured images folder
2. **Send** each image to the configured vision-language model
3. **Clean** the raw output using the `text_extraction` prompt
4. **Save** as Markdown, with model/confidence/timestamp in frontmatter

### Output Format

```markdown
---
title: 1863-04-15_001
extracted_at: '2026-01-15T14:32:00Z'
model: qwen-vl-max
confidence: 0.92
---

April 15th, 1863

Dear Sarah...
```

---

## Stage 2: Entity Extraction

**Purpose:** Identify named entities with context.

**Input:** Transcription files
**Output:** JSON files in `entities/`, plus `entities/consolidated.json`

### Process

1. **Read** transcription text
2. **Analyze** with the LLM to find entities
3. **Classify** each entity by type
4. **Generate** contextual descriptions (if `entity_context: true`)
5. **Save** per-document JSON, then consolidate across all documents

### Output Format

```json
{
  "source_image": "1863-04-15_001",
  "extracted_at": "2026-01-15T14:32:00Z",
  "entities": [
    {
      "text": "Sarah",
      "type": "PERSON",
      "context": "Person; the recipient of the letter, likely the writer's wife"
    }
  ]
}
```

---

## Stage 3: Translation (optional)

**Purpose:** Translate transcriptions to a target language.

**Input:** Transcription files
**Output:** Markdown files in `translations/`

### Process

1. **Read** the transcription text
2. **Send** to Google Translate (via `deep-translator`)
3. **Translate** from source to target language
4. **Save** translated text as Markdown

### Configuration

```yaml
translate:
  enabled: true
  source_languages:
    - "en"
  target_language: "es"
  default_tab: "transcription"
```

This stage isn't part of `ficherito process` — run `ficherito translate`
explicitly, then `ficherito build` to include it on the site.

---

## Stage 4: Build

**Purpose:** Create the static website.

**Input:** Transcriptions, entities, translations (all optional except transcriptions)
**Output:** An Eleventy site in `site/`, built to `site/_site/`

### Process

1. **Load** transcriptions, entities, and translations
2. **Sort** documents chronologically (via `undate`-aware date parsing)
3. **Emit** each document as Markdown + frontmatter into `site/src/documents/`,
   plus compressed images and `_data/site.json` / `_data/allEntities.json`
4. **Run** `npm run build` inside `site/` — Eleventy renders the pages,
   then Pagefind indexes them (via an `eleventy.after` hook)

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        INPUT                                 │
├──────────────────────────────────────────────────────────────┤
│  images/  (local folder)                                     │
│  ├── image_001.jpg                                           │
│  ├── image_002.jpg                                           │
│  └── ...                                                     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    INTERMEDIATE FILES                        │
├──────────────────────────────────────────────────────────────┤
│  transcriptions/       entities/            translations/    │
│  ├── doc_001.md        ├── doc_001.json     ├── doc_001.md   │
│  ├── doc_002.md        ├── doc_002.json     └── ...          │
│  └── ...                └── consolidated.json                │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        OUTPUT                                │
├──────────────────────────────────────────────────────────────┤
│  site/_site/                                                 │
│  ├── index.html          (password gate)                     │
│  ├── main.html            (search)                           │
│  ├── documents/<id>/                                          │
│  ├── browse/{dates,entities}.html                            │
│  └── pagefind/            (search index)                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Running Pipeline Stages

### Full Pipeline

```bash
ficherito process
```

### Individual Stages

```bash
ficherito extract      # Stage 1 only
ficherito entities     # Stage 2 only
ficherito translate    # Stage 3 only (opt-in, not part of `process`)
ficherito build         # Stage 4 only
```

### Dependencies

| Stage | Requires |
|-------|----------|
| Extract | Images in `dataset.images_dir` |
| Entities | Transcriptions |
| Translate | Transcriptions |
| Build | Transcriptions (entities/translations optional) |

---

## Resume Capability

`extract` and `entities` save output immediately per document and skip
already-processed files, so an interrupted run can just be re-run:

```bash
ficherito extract
# Skipped 450 images with existing transcriptions
# Extracting text (50/500)...
```

---

## Next Steps

- **[HTR and OCR](htr-ocr.md)** - How text extraction works
- **[Named Entities](named-entities.md)** - Understanding entity extraction
- **[Building Sites](../usage/building-sites.md)** - The Eleventy build in detail
