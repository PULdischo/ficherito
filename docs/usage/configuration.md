# Configuration

This guide covers all configuration options for Ficherito projects.

---

## Configuration Files

Ficherito uses two configuration files:

| File | Purpose | Version Control |
|------|---------|-----------------|
| `ficherito.yaml` | Project settings | ✅ Commit to Git |
| `.env` | API key | ❌ Never commit |

---

## ficherito.yaml Reference

```yaml
# =============================================================================
# DATASET CONFIGURATION
# =============================================================================
dataset:
  # Local folder of document images (required)
  images_dir: "images"

  # Search subfolders recursively (default: false)
  recursive: false

# =============================================================================
# PROCESSING OPTIONS
# =============================================================================
processing:
  # Whether to extract named entities after transcription
  extract_entities: true

  # Include contextual descriptions for entities
  # e.g., "Person; the plaintiff in the legal case" instead of just "Person"
  entity_context: true

  # Maximum tokens the model may generate per request (transcription and
  # entity extraction). Many providers default to a low limit (e.g.
  # 512-1024) when this isn't set, which silently truncates transcriptions
  # of multi-page or dense document images -- and can leave entity
  # extraction with no valid JSON to parse. Raise this if transcriptions
  # are getting cut off or entities aren't showing up. (default: 4096)
  max_output_tokens: 4096

# =============================================================================
# CUSTOM PROMPTS
# =============================================================================
prompts:
  # Prompt for cleaning up raw OCR/HTR text
  # Available variable: {raw_text}
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

  # Prompt for extracting named entities
  # Available variable: {document_text}
  ner_extraction: |
    You are a historical document analyst specializing in named entity recognition.
    Extract all named entities from the following transcribed document text.

    For each entity, provide:
    1. The exact text as it appears
    2. The entity type (PERSON, ORGANIZATION, LOCATION, DATE, MONEY,
       LEGAL_TERM, EVENT, DOCUMENT, OCCUPATION, RELATIONSHIP)
    3. A contextual description explaining the entity's role in THIS document

    Document text:
    {document_text}

    Return entities as a JSON array:
    [
      {
        "text": "John Smith",
        "type": "PERSON",
        "context": "Person; the plaintiff filing the complaint"
      }
    ]

# =============================================================================
# TRANSLATION OPTIONS
# =============================================================================
translate:
  # Enable/disable translation
  enabled: false

  # Source language(s) - ISO 639-1 codes
  source_languages:
    - "es"

  # Target language - ISO 639-1 code
  target_language: "en"

  # Which tab to show by default on document pages
  # Options: "transcription" or "translation"
  default_tab: "transcription"

# =============================================================================
# WEBSITE OPTIONS
# =============================================================================
website:
  # Site title (appears in header and browser tab)
  title: "Document Collection"

  # Emoji shown next to the title
  emoji: "🐟"

  # Header/hero background color
  background_color: "#1e3a5f"

  # Accent color for links and buttons
  accent_color: "#2563eb"

  # Client-side password protection (not encryption — see building-sites.md)
  password: "changeme"

  # Enable/disable Pagefind search
  enable_search: true

  # Enable/disable the two browse pages
  enable_browse_dates: true
  enable_browse_entities: true

  # Default sort order on browse pages
  default_sort: "date"

  # Optional: Netlify site ID, for `ficherito deploy`
  netlify_site_id: ""

# =============================================================================
# OUTPUT DIRECTORIES
# =============================================================================
output:
  # Where to save transcriptions
  transcriptions_dir: "transcriptions"

  # Where to save translations
  translations_dir: "translations"

  # Where to save entity extractions
  entities_dir: "entities"

  # Where the Eleventy (11ty) site project lives
  eleventy_dir: "site"

  # Where the built static site ends up (Eleventy's output dir)
  site_dir: "site/_site"
```

---

## Environment Variables (.env)

```bash
# OpenAI-compatible LLM endpoint (DashScope, OpenAI, local, etc.)
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=qwen-vl-max

# Netlify token for deployment (optional — GitHub Pages doesn't need this)
NETLIFY_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NETLIFY_SITE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

```{warning}
**Never commit `.env` to version control!** `ficherito init` adds it to `.gitignore` for you.
```

---

## Configuration Precedence

1. Default values (built into Ficherito's `FicheritoConfig` model)
2. `ficherito.yaml` in the current directory
3. Command-line options, where a command exposes them

For example:
```bash
# Overrides output.site_dir for this run only
ficherito build --output ./my-custom-site
```

---

## Validating Configuration

```bash
ficherito validate
```

This checks:

- ✅ Configuration file syntax
- ✅ `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OPENAI_MODEL`
- ✅ Images folder exists

---

## Examples

### Minimal Configuration

```yaml
dataset:
  images_dir: "images"
```

### Research Project with Password Protection

```yaml
dataset:
  images_dir: "images"

processing:
  extract_entities: true
  entity_context: true

website:
  title: "Smith Family Civil War Correspondence"
  password: "research2026"
```

### Public Collection with Translation

```yaml
dataset:
  images_dir: "images"

processing:
  extract_entities: true

translate:
  enabled: true
  source_languages: ["es"]
  target_language: "en"
  default_tab: "translation"

website:
  title: "Historic Newspaper Archive"
  password: ""  # Public access
```

---

## Next Steps

- **[Processing Documents](processing-documents.md)** - Learn about the processing pipeline
- **[Transcription](transcription.md)** - Fine-tune text extraction
- **[Troubleshooting](../help/troubleshooting.md)** - Solve common issues
