# Ficherito - Historical Document Analysis CLI

## Overview

Ficherito is a Python CLI application for extracting, analyzing, and presenting handwritten text from historical document images. It processes a local folder of images, performs OCR/HTR and named entity extraction, optionally translates transcriptions, and builds a searchable, editable static website (Eleventy + Pagefind + Sveltia CMS) for browsing the collection.

---

## Table of Contents

1. [Installation & Distribution](#installation--distribution)
2. [Configuration](#configuration)
3. [Core Features](#core-features)
4. [Data Pipeline](#data-pipeline)
5. [Output Structure](#output-structure)
6. [Static Website](#static-website)
7. [Technical Stack](#technical-stack)
8. [CLI Commands](#cli-commands)
9. [Error Handling](#error-handling)
10. [Future Considerations](#future-considerations)

---

## Installation & Distribution

### PyPI Publication

- **Package Name**: `ficherito`
- **Entry Point**: `ficherito` CLI command
- **Python Version**: 3.10+
- **License**: MIT (or specify preferred license)

### Installation

```bash
pip install ficherito
```

### Development Installation

```bash
git clone https://github.com/username/ficherito.git
cd ficherito
pip install -e ".[dev]"
```

---

## Configuration

### Config File: `ficherito.yaml`

```yaml
# Dataset Configuration
dataset:
  images_dir: "images"             # Local folder of document images
  recursive: false                 # Search subfolders recursively

# Processing Options
processing:
  extract_entities: true           # Enable/disable entity extraction
  entity_context: true             # Include contextual descriptions for entities

# Prompts
prompts:
  # Prompt for text extraction post-processing and cleanup
  text_extraction: |
    You are a historical document transcription assistant. Given the raw OCR/HTR 
    output from a handwritten document, clean up and correct the text while:
    
    1. Preserving the original spelling, including archaic forms
    2. Fixing obvious OCR errors (e.g., 'tbe' → 'the')
    3. Maintaining original line breaks where meaningful
    4. Preserving original punctuation style
    5. Marking unclear or illegible portions with [?] or [illegible]
    6. Expanding common abbreviations only if unambiguous
    
    Raw OCR text:
    {raw_text}
    
    Cleaned transcription:

  # Prompt for named entity recognition with context
  ner_extraction: |
    You are a historical document analyst specializing in named entity recognition.
    Extract all named entities from the following transcribed document text.
    
    For each entity, provide:
    1. The exact text as it appears
    2. The entity type (PERSON, ORGANIZATION, LOCATION, DATE, MONEY, LEGAL_TERM, EVENT, DOCUMENT, OCCUPATION, RELATIONSHIP)
    3. A contextual description explaining the entity's role in THIS document
       (e.g., not just "Person" but "Person; the plaintiff filing the complaint")
    
    Document text:
    {document_text}
    
    Return entities as a JSON array:
    [
      {
        "text": "John Smith",
        "type": "PERSON", 
        "context": "Person; the plaintiff filing the complaint against the estate"
      },
      ...
    ]

# Translation Configuration
translate:
  enabled: false
  source_languages:
    - "es"
  target_language: "en"
  default_tab: "transcription"     # or "translation"

# Output Configuration
output:
  transcriptions_dir: "transcriptions"
  translations_dir: "translations"
  entities_dir: "entities"
  eleventy_dir: "site"             # Eleventy (11ty) site project
  site_dir: "site/_site"           # Built static site (Eleventy output)

# Website Configuration
website:
  title: "Document Collection"
  emoji: "🐟"
  background_color: "#1e3a5f"
  accent_color: "#2563eb"
  password: "changeme"             # Simple client-side password protection
  enable_search: true              # Pagefind search
  enable_browse_dates: true
  enable_browse_entities: true
  default_sort: "date"
```

### Environment File: `.env`

```bash
# OpenAI-compatible LLM endpoint (DashScope, OpenAI, local, etc.)
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=qwen-vl-max
```

---

## Core Features

### 1. Handwritten Text Recognition (HTR)

- **Input**: Images from a local folder (`dataset.images_dir`), including PDFs rendered to page images
- **Model**: Any OpenAI-compatible vision model (DashScope/Qwen-VL by default, configurable via `.env`)
- **Output**: Plain text transcription

#### Supported Image Formats
- JPEG, PNG, TIFF, WebP, HEIC
- Automatic format detection

#### Processing Pipeline
1. Load image from the local folder (PDFs are rendered to page images first)
2. Convert to base64 and send to the configured vision model
3. Post-process text (basic cleanup)
4. Save to a Markdown transcription file

### 2. Entity Extraction

- **Trigger**: Enabled via `processing.extract_entities` in config
- **Output Format**: Entities with contextual descriptions

#### Entity Types
| Type | Example | Context Example |
|------|---------|-----------------|
| PERSON | "John Smith" | "Person; the plaintiff in the case" |
| ORGANIZATION | "First National Bank" | "Organization; the defendant's employer" |
| LOCATION | "Springfield" | "Location; where the incident occurred" |
| DATE | "March 15, 1892" | "Date; when the contract was signed" |
| MONEY | "$500" | "Money; amount of disputed payment" |
| LEGAL_TERM | "habeas corpus" | "Legal term; basis for the appeal" |

#### Context Generation
- Uses LLM to understand document context
- Generates human-readable role descriptions
- Links entities across documents when possible

### 3. Translation

- **Trigger**: Enabled via `translate.enabled` in config
- **Engine**: Google Translate (via `deep-translator`)
- **Output**: A parallel Markdown translation file per document, shown as a tab
  alongside the original transcription on the document page
- Source language(s) and target language are configurable (`translate.source_languages`,
  `translate.target_language`); `translate.default_tab` controls which text is shown first

---

## Data Pipeline

```
┌─────────────────┐
│  Local Folder   │
│  of Images      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Image Loader   │
│  (+ PDF render) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTR Engine     │
│  (Text Extract) │
└────────┬────────┘
         │
         ├──────────────────────┬──────────────────────┐
         ▼                      ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Save .md       │    │ Entity Extract  │    │  Translate      │
│  Transcriptions │    │ (if enabled)    │    │  (if enabled)   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                       │
         └──────────────────────┴───────────────────────┘
                    ▼
         ┌─────────────────┐
         │  Emit Markdown  │
         │  + Frontmatter  │
         │  into site/     │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Eleventy +     │
         │  Pagefind       │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  site/_site/    │
         └─────────────────┘
```

---

## Output Structure

```
project/
├── ficherito.yaml              # Configuration file
├── .env                        # API keys (git-ignored)
├── images/                     # Source document images (git-ignored)
├── transcriptions/             # Extracted text files
│   ├── img001.md
│   ├── img002.md
│   └── ...
├── translations/               # Translated text files (if enabled)
│   ├── img001.md
│   └── ...
├── entities/                   # Entity data (JSON)
│   ├── img001.json
│   ├── img002.json
│   └── consolidated.json       # All entities merged
└── site/                       # Eleventy site (scaffolded on first build)
    ├── admin/config.yml         # Sveltia CMS config
    ├── .eleventy.js
    ├── package.json
    ├── src/
    │   ├── documents/           # Emitted document content (.md, tracked in git)
    │   │   ├── img001.md
    │   │   ├── img002.md
    │   │   └── documents.json   # Shared layout/permalink for the collection
    │   ├── assets/
    │   │   ├── css/style.css
    │   │   └── images/documents/  # Compressed document images (tracked in git)
    │   ├── _data/
    │   │   ├── site.json         # Website config (emitted by `build`)
    │   │   └── allEntities.json  # Consolidated entities (emitted by `build`)
    │   ├── index.njk              # Password gate
    │   ├── search.njk             # Search page (-> main.html)
    │   └── browse/
    │       ├── dates.njk
    │       └── entities.njk
    └── _site/                    # Built static website (git-ignored)
        ├── index.html
        ├── main.html
        ├── documents/<id>/index.html
        ├── browse/{dates,entities}.html
        ├── assets/
        └── pagefind/              # Search index
```

### Transcription File Format

**File**: `transcriptions/img001.md`

```
The honorable court is hereby petitioned
by the undersigned plaintiff, John Smith,
residing at 123 Main Street, Springfield...
```

### Entity JSON Format

**File**: `entities/img001.json`

```json
{
  "source_image": "img001",
  "extracted_at": "2024-01-15T10:30:00Z",
  "entities": [
    {
      "text": "John Smith",
      "type": "PERSON",
      "context": "Person; the plaintiff in the case",
      "positions": [{"start": 45, "end": 55}],
      "confidence": 0.92
    },
    {
      "text": "Springfield",
      "type": "LOCATION", 
      "context": "Location; plaintiff's place of residence",
      "positions": [{"start": 78, "end": 89}],
      "confidence": 0.88
    }
  ]
}
```

---

## Static Website

### Architecture

- **Generator**: [Eleventy](https://www.11ty.dev/) (11ty), Nunjucks templates
- **Search**: [Pagefind](https://pagefind.app/), loaded off the critical path
  (a plain `<input>` renders immediately; the Pagefind UI bundle loads via
  `requestIdleCallback`, or immediately on focus/typing)
- **Content Editing**: [Sveltia CMS](https://github.com/sveltia/sveltia-cms) at `/admin/`,
  committing directly to `site/src/documents/*.md` via the GitHub API
- **Image Viewer**: OpenSeaDragon
- **Styling**: Plain CSS (`site/src/assets/css/style.css`)
- **Deployment**: GitHub Pages via GitHub Actions (`.github/workflows/deploy.yml`),
  which only runs Eleventy + Pagefind on already-committed content — the
  Python pipeline is never re-run in CI

`ficherito build` does not render HTML itself: it emits Markdown +
frontmatter + images into `site/src/documents/` and `site/src/assets/images/documents/`,
writes `site/src/_data/site.json` and `allEntities.json`, then runs `npm run
build` inside `site/`, which runs Eleventy and then Pagefind via an
`eleventy.after` build hook.

### Pages

#### 1. Index Page (Password Protection)

- Simple client-side password gate
- Stores auth in sessionStorage
- Redirects to main page on success

```html
<!-- Simplified password check -->
<form id="auth-form">
  <input type="password" id="password" placeholder="Enter password">
  <button type="submit">Enter</button>
</form>
<script>
  // Simple hash comparison (not cryptographically secure)
  // Suitable for basic access control, not sensitive data
</script>
```

#### 2. Main Page (Search)

**Features:**
- Collection stats (document/entity counts)
- Full-text search via Pagefind, loaded off the critical path (see [Static Website](#static-website))
- Dates are parsed with `undate`, supporting partial precision (year-only,
  year-month, or full day); documents without parseable dates sort to the end

**Layout:**
```
┌─────────────────────────────────────────┐
│  [Logo]  Document Collection            │
│  Search | Browse by Date | Browse by    │
│                            Entity       │
├─────────────────────────────────────────┤
│         Documents      Entities         │
│           1,204           312           │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │  🔍 Search documents...         │    │
│  └─────────────────────────────────┘    │
│         (Pagefind results)              │
└─────────────────────────────────────────┘
```

#### 3. Document Page

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  ← Back to Browse          Document: img001.jpg         │
├────────────────────────────┬────────────────────────────┤
│                            │  Transcription             │
│                            │  ──────────────            │
│   [OpenSeaDragon Viewer]   │  The honorable court is    │
│                            │  hereby petitioned by the  │
│   ┌──────────────────┐     │  undersigned plaintiff...  │
│   │                  │     │                            │
│   │    Zoomable      │     ├────────────────────────────┤
│   │     Image        │     │  Entities                  │
│   │                  │     │  ────────                  │
│   │                  │     │  👤 John Smith             │
│   └──────────────────┘     │     → Plaintiff in case    │
│                            │  📍 Springfield            │
│   [+] [-] [⟳] [⛶]         │     → Plaintiff's residence│
│                            │                            │
└────────────────────────────┴────────────────────────────┘
```

#### 4. Browse by Dates

- Calendar or timeline view
- Groups documents by date/date range
- Handles uncertain dates gracefully

#### 5. Browse by Entities

- Faceted browse by entity type
- Click entity to see all documents mentioning it
- Shows context for each mention

### OpenSeaDragon Integration

```javascript
// Initialize viewer
var viewer = OpenSeadragon({
    id: "openseadragon-viewer",
    prefixUrl: "/assets/openseadragon/images/",
    tileSources: {
        type: 'image',
        url: '/documents/img001/image.jpg'
    },
    // Or use Deep Zoom Image (DZI) for large images
    // tileSources: '/documents/img001/tiles/img001.dzi'
});
```

### Pagefind Integration

Indexing is wired into the Eleventy build itself (`site/.eleventy.js`), not a
separate manual step:

```javascript
// site/.eleventy.js
eleventyConfig.on("eleventy.after", () => {
    if (process.env.ENABLE_SEARCH === "false") return;
    execSync("npx pagefind --site _site", { stdio: "inherit" });
});
```

The search page (`main.html`) loads the Pagefind UI bundle off the critical
path — a plain `<input>` renders immediately, and `pagefind-ui.js` is
injected via `requestIdleCallback` (or immediately on focus/typing) rather
than a blocking `<script>` tag, so search never delays page load.

---

## Technical Stack

### Core Dependencies

| Package | Purpose |
|---------|---------|
| `typer` | CLI framework |
| `pyyaml` | Config parsing |
| `pydantic` / `pydantic-settings` | Config validation |
| `python-dotenv` | Environment variables |
| `undate` | Partial/uncertain date modeling |
| `Pillow` / `pillow-heif` | Image processing |
| `pymupdf` | PDF-to-image rendering |
| `openai` | OpenAI-compatible LLM client (HTR, entities) |
| `deep-translator` | Translation |
| `rich` | CLI output formatting |
| `httpx`, `tqdm`, `markdown` | Supporting utilities |
| `netlify-python` | Optional Netlify deployment |

### Development Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `ruff` | Linting |
| `mypy` | Type checking |
| `pre-commit` | Git hooks |

### External Tools (for site build)

| Tool | Purpose |
|------|---------|
| Node.js 20+ | Runs the Eleventy site build |
| Eleventy (11ty) | Static site generator |
| Pagefind | Static search indexing |
| Sveltia CMS | Browser-based content editing |
| OpenSeaDragon | Image viewer (JS library) |

---

## CLI Commands

### Main Commands

```bash
# Initialize a new project
ficherito init

# Process dataset (full pipeline)
ficherito process

# Individual steps
ficherito extract          # Run HTR only
ficherito entities         # Extract entities only
ficherito translate        # Translate transcriptions
ficherito build            # Emit content and build the 11ty + Pagefind site

# Utility commands
ficherito validate         # Validate config and connections
ficherito status           # Show processing status
ficherito serve            # Local preview server
ficherito deploy           # Deploy site to Netlify
```

### Command Options

```bash
# Process with options
ficherito process \
  --config custom-config.yaml \
  --limit 100 \
  --skip-entities \
  --verbose

# Build with options
ficherito build \
  --output ./custom_site \
  --base-url "/docs/"

# Serve locally
ficherito serve --port 8080
```

### Example Session

```bash
# 1. Initialize project
$ ficherito init
Created ficherito.yaml
Created .env.example
Copy .env.example to .env and add your API keys.

# 2. Configure (edit files)
$ nano ficherito.yaml
$ cp .env.example .env && nano .env
# Add images to images/

# 3. Validate setup
$ ficherito validate
✓ Config file valid
✓ LLM base URL: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
✓ API key found
✓ Images folder: images
Ready to process!

# 4. Run full pipeline
$ ficherito process
Extracting text... ━━━━━━━━━━━━━━━━━━━━ 100%
Extracting entities... ━━━━━━━━━━━━━━━━ 100%
Building website... ━━━━━━━━━━━━━━━━━━━ 100%

Complete! Site built to site/_site/

# 5. Preview
$ ficherito serve
Serving at http://localhost:8000
```

---

## Error Handling

### Configuration Errors

| Error | Message | Resolution |
|-------|---------|------------|
| Missing config | `ficherito.yaml not found` | Run `ficherito init` |
| Invalid YAML | `Config parse error at line X` | Fix YAML syntax |
| Missing required field | `dataset.images_dir is required` | Add missing field |

### API Errors

| Error | Message | Resolution |
|-------|---------|------------|
| Missing API key | `OPENAI_API_KEY not set` | Add it to `.env` |
| LLM request failure | `API error: {details}` | Check API key/quota/base URL |
| Images folder missing | `Images directory not found` | Check `dataset.images_dir` |

### Processing Errors

| Error | Message | Resolution |
|-------|---------|------------|
| Image load failure | `Failed to load image: {path}` | Check image format |
| HTR failure | `Text extraction failed for {image}` | Check image quality |
| Entity extraction failure | `Entity extraction failed` | Check model availability |

### Graceful Degradation

- Continue processing on individual image failures
- Log errors and create error report
- Build site with available data

---

## Future Considerations

### Potential Enhancements

1. **Multi-language Support**
   - Configurable HTR models per language
   - Multilingual entity extraction

2. **Collaborative Editing**
   - Web interface for transcription corrections
   - Sync corrections back to source

3. **Advanced Visualization**
   - Network graphs for entity relationships
   - Geographic mapping for location entities

4. **Export Options**
   - TEI/XML export
   - IIIF manifest generation
   - CSV/Excel export

5. **Batch Processing**
   - Resume interrupted processing
   - Incremental updates
   - Parallel processing

6. **Model Customization**
   - Fine-tuned HTR models
   - Custom entity types
   - Domain-specific prompts

---

## Project Structure

```
ficherito/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── ficherito/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py                 # Typer CLI definitions
│       ├── config.py              # Config loading/validation
│       ├── dataset.py             # Local image folder handling (+ PDF render)
│       ├── pipeline.py            # Pipeline orchestration
│       ├── htr/
│       │   ├── __init__.py
│       │   ├── engine.py          # HTR processing
│       │   └── models.py          # Model loading
│       ├── entities/
│       │   ├── __init__.py
│       │   └── extractor.py       # Entity extraction + consolidation
│       ├── translation/
│       │   ├── __init__.py
│       │   └── translator.py      # Translation
│       ├── site/
│       │   ├── __init__.py
│       │   ├── builder.py         # Emits content, runs Eleventy + Pagefind
│       │   └── scaffold/          # Bundled Eleventy/Pagefind/Sveltia project
│       │       ├── .eleventy.js
│       │       ├── package.json
│       │       ├── admin/config.yml
│       │       └── src/
│       │           ├── documents/documents.json
│       │           ├── _includes/{layouts,partials}/
│       │           ├── index.njk
│       │           ├── search.njk
│       │           └── browse/{dates,entities}.njk
│       └── utils/
│           ├── __init__.py
│           ├── dates.py           # undate-based date parsing
│           ├── images.py          # Image utilities
│           └── logging.py         # Logging setup
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_dates.py
    └── test_text.py
```

---

## Appendix

### A. Sample pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ficherito"
version = "0.1.0"
description = "Historical document analysis CLI"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [
    { name = "Your Name", email = "you@example.com" }
]
dependencies = [
    "typer[all]>=0.12",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",
    "undate>=0.8",
    "Pillow>=10.0",
    "pillow-heif>=0.16",
    "pymupdf>=1.24",
    "openai>=1.0",
    "rich>=13.0",
    "httpx>=0.25",
    "deep-translator>=1.11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[project.scripts]
ficherito = "ficherito.cli:app"

[tool.hatch.build.targets.wheel]
packages = ["src/ficherito"]
```

### B. Qwen-VL Model Options

Ficherito talks to any OpenAI-compatible vision endpoint (configured via
`.env`); DashScope's Qwen-VL models are the default:

| Model | Best For | Notes |
|-------|----------|-------|
| qwen-vl-max | Best quality | Highest accuracy for historical docs |
| qwen-vl-plus | Balanced | Good speed/quality tradeoff |
| qwen-vl | Fast | Quick processing, lower accuracy |

### C. Entity Extraction Prompts

```python
ENTITY_CONTEXT_PROMPT = """
Given the following document text and extracted entity, provide a brief 
contextual description of the entity's role in this document.

Document: {document_text}
Entity: {entity_text}
Entity Type: {entity_type}

Provide a context description in the format: "{type}; {role description}"
Example: "Person; the plaintiff in the case"

Context:
"""
```

---

*Last Updated: August 2026*
*Version: 0.1.0-spec*
