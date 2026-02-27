# Flatfish - Historical Document Analysis CLI

## Overview

Flatfish is a Python CLI application for extracting, analyzing, and presenting handwritten text from historical document images. It processes images from HuggingFace datasets, performs OCR and entity extraction, generates AI-powered summaries with temporal analysis, and builds a searchable static website for browsing the collection.

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

- **Package Name**: `flatfish`
- **Entry Point**: `flatfish` CLI command
- **Python Version**: 3.10+
- **License**: MIT (or specify preferred license)

### Installation

```bash
pip install flatfish
```

### Development Installation

```bash
git clone https://github.com/username/flatfish.git
cd flatfish
pip install -e ".[dev]"
```

---

## Configuration

### Config File: `flatfish.yaml`

```yaml
# Dataset Configuration
dataset:
  source: "username/dataset-name"  # HuggingFace dataset address
  splits:
    - "train"
    - "test"
  image_column: "image"            # Column name containing images
  
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

  # Prompt for sequential document summary
  summary: |
    You are a historian analyzing a sequence of related documents. The documents 
    are provided in chronological order with their dates/timestamps.
    
    Analyze these documents and provide:
    
    ## Timeline of Events
    A chronological list of key events mentioned or implied across the documents.
    Include dates (exact or approximate) and brief descriptions.
    
    ## Key Changes
    Identify significant changes between documents:
    - Shifts in tone, position, or claims
    - New information introduced
    - Contradictions or amendments to previous statements
    - Changes in parties involved
    
    ## Research Questions
    Suggest 3-5 historical research questions that emerge from these documents:
    - Gaps in the record that warrant investigation
    - Connections to broader historical contexts
    - Potential related sources to consult
    - Unanswered questions about motivations or outcomes
    
    Documents:
    {documents}
  
# Qwen/DashScope Configuration
summary:
  enabled: true
  model: "qwen-vl-max"             # or other Qwen model
  include_timeline: true
  include_key_changes: true
  include_research_questions: true

# Output Configuration
output:
  transcriptions_dir: "transcriptions"
  site_dir: "_site"
  
# Website Configuration
website:
  title: "Document Collection"
  password: "changeme"             # Simple password protection
  enable_search: true              # Pagefind search
  enable_browse_dates: true
  enable_browse_entities: true
```

### Environment File: `.env`

```bash
# HuggingFace Access
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx

# DashScope API (for Qwen)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx

# Optional: Custom model endpoints
# HTR_MODEL_ENDPOINT=https://...
```

---

## Core Features

### 1. Handwritten Text Recognition (HTR)

- **Input**: Images from HuggingFace dataset
- **Model**: Qwen-VL via DashScope API
- **Output**: Plain text transcription

#### Supported Image Formats
- JPEG, PNG, TIFF, WebP, HEIC
- Automatic format detection

#### Processing Pipeline
1. Load image from dataset
2. Convert to base64 and send to Qwen-VL
3. Post-process text (basic cleanup)
4. Save to text file

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

### 3. Sequential Document Summary (Qwen/DashScope)

- **API**: DashScope (Alibaba Cloud)
- **Model**: Qwen-VL or Qwen-Plus

#### Summary Components

1. **Timeline of Events**
   - Chronological ordering of events mentioned
   - Date normalization and sequencing
   - Gap identification

2. **Key Changes Analysis**
   - Document-to-document comparisons
   - Tracking of evolving narratives
   - Identification of contradictions or amendments

3. **Research Questions**
   - AI-generated suggestions for further research
   - Identification of gaps in the record
   - Cross-reference suggestions

#### API Request Structure
```python
{
    "model": "qwen-vl-max",
    "messages": [
        {
            "role": "system",
            "content": "You are a historical document analyst..."
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Document 1 (1892-03-15): ..."},
                {"type": "text", "text": "Document 2 (1892-03-20): ..."},
                # ... sequential documents with timestamps
            ]
        }
    ]
}
```

---

## Data Pipeline

```
┌─────────────────┐
│  HuggingFace    │
│    Dataset      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Image Loader   │
│  (by split)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTR Engine     │
│  (Text Extract) │
└────────┬────────┘
         │
         ├──────────────────────┐
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  Save .txt      │    │ Entity Extract  │
│  Transcriptions │    │ (if enabled)    │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
         ┌─────────────────┐
         │  Qwen Summary   │
         │  (DashScope)    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Build Static   │
         │    Website      │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │    _site/       │
         └─────────────────┘
```

---

## Output Structure

```
project/
├── flatfish.yaml              # Configuration file
├── .env                       # API keys (git-ignored)
├── transcriptions/            # Extracted text files
│   ├── img001.txt
│   ├── img002.txt
│   └── ...
├── entities/                  # Entity data (JSON)
│   ├── img001.json
│   ├── img002.json
│   └── consolidated.json      # All entities merged
├── summaries/                 # Qwen-generated summaries
│   ├── timeline.json
│   ├── key_changes.json
│   ├── research_questions.json
│   └── full_summary.md
└── _site/                     # Built static website
    ├── index.html             # Password-protected entry
    ├── main.html              # Search & browse interface
    ├── documents/
    │   ├── img001/
    │   │   ├── index.html     # Document viewer page
    │   │   └── tiles/         # OpenSeaDragon tiles
    │   └── ...
    ├── browse/
    │   ├── dates.html
    │   └── entities.html
    ├── assets/
    │   ├── css/
    │   ├── js/
    │   └── images/
    └── pagefind/              # Search index
```

### Transcription File Format

**File**: `transcriptions/img001.txt`

```
[Transcription of img001.jpg]
[Extracted: 2024-01-15T10:30:00Z]
[Confidence: 0.94]

---

The honorable court is hereby petitioned
by the undersigned plaintiff, John Smith,
residing at 123 Main Street, Springfield...
```

### Entity JSON Format

**File**: `entities/img001.json`

```json
{
  "source_image": "img001.jpg",
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

- **Generator**: Jinja2 templates
- **Search**: Pagefind (static search)
- **Image Viewer**: OpenSeaDragon
- **Styling**: Tailwind CSS (or simple custom CSS)

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

#### 2. Main Page

**Features:**
- Default sort: chronological by date (extracted from filename or metadata)
- Date parsing supports common formats: `YYYY-MM-DD`, `YYYYMMDD`, `MM-DD-YYYY`, etc.
- Documents without parseable dates sorted to end

**Layout:**
```
┌─────────────────────────────────────────┐
│  [Logo]  Document Collection    [About] │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │  🔍 Search documents...         │    │
│  └─────────────────────────────────┘    │
├─────────────────────────────────────────┤
│  Sort: [Date ▼] [Name] [Relevance]      │
│  Browse by:  [Dates] [Entities]         │
├─────────────────────────────────────────┤
│  Timeline Summary                       │
│  ─────────────────                      │
│  • 1892-03-15: Initial petition filed   │
│  • 1892-03-20: Response submitted       │
│  • ...                                  │
├─────────────────────────────────────────┤
│  Research Questions                     │
│  ─────────────────                      │
│  • What prompted the sudden change...   │
│  • ...                                  │
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

```bash
# Build search index (run after site generation)
npx pagefind --site _site --output-subdir pagefind
```

```html
<!-- In main.html -->
<link href="/pagefind/pagefind-ui.css" rel="stylesheet">
<script src="/pagefind/pagefind-ui.js"></script>
<div id="search"></div>
<script>
    new PagefindUI({ element: "#search", showImages: true });
</script>
```

---

## Technical Stack

### Core Dependencies

| Package | Purpose | Version |
|---------|---------|---------||
| `typer` | CLI framework | ^0.12 |
| `pyyaml` | Config parsing | ^6.0 |
| `python-dotenv` | Environment variables | ^1.0 |
| `datasets` | HuggingFace datasets | ^2.0 |
| `Pillow` | Image processing | ^10.0 |
| `dashscope` | Qwen VL/NLP API | ^1.0 |
| `jinja2` | Template engine | ^3.0 |
| `rich` | CLI output formatting | ^13.0 |

### Development Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `black` | Code formatting |
| `ruff` | Linting |
| `mypy` | Type checking |
| `pre-commit` | Git hooks |

### External Tools (for site build)

| Tool | Purpose |
|------|---------|
| Pagefind | Static search indexing |
| OpenSeaDragon | Image viewer (JS library) |

---

## CLI Commands

### Main Commands

```bash
# Initialize a new project
flatfish init

# Process dataset (full pipeline)
flatfish process

# Individual steps
flatfish extract          # Run HTR only
flatfish entities         # Extract entities only
flatfish summarize        # Generate Qwen summary only
flatfish build            # Build static site only

# Utility commands
flatfish validate         # Validate config and connections
flatfish status           # Show processing status
flatfish publish           # Local preview server
```

### Command Options

```bash
# Process with options
flatfish process \
  --config custom-config.yaml \
  --split train \
  --limit 100 \
  --skip-entities \
  --skip-summary \
  --verbose

# Build with options
flatfish build \
  --output ./custom_site \
  --no-search \
  --base-url "/docs/"

# Serve locally
flatfish publish --port 8080
```

### Example Session

```bash
# 1. Initialize project
$ flatfish init
Created flatfish.yaml
Created .env.example
Copy .env.example to .env and add your API keys.

# 2. Configure (edit files)
$ nano flatfish.yaml
$ cp .env.example .env && nano .env

# 3. Validate setup
$ flatfish validate
✓ Config file valid
✓ HuggingFace token valid
✓ Dataset accessible: username/my-documents
✓ DashScope API key valid
Ready to process!

# 4. Run full pipeline
$ flatfish process
Loading dataset... ━━━━━━━━━━━━━━━━━━━━ 100%
Extracting text... ━━━━━━━━━━━━━━━━━━━━ 100%
Extracting entities... ━━━━━━━━━━━━━━━━ 100%
Generating summary... ━━━━━━━━━━━━━━━━━ 100%
Building site... ━━━━━━━━━━━━━━━━━━━━━━ 100%

Complete! Site built to _site/

# 5. Preview
$ flatfish publish
Serving at http://localhost:8000
```

---

## Error Handling

### Configuration Errors

| Error | Message | Resolution |
|-------|---------|------------|
| Missing config | `flatfish.yaml not found` | Run `flatfish init` |
| Invalid YAML | `Config parse error at line X` | Fix YAML syntax |
| Missing required field | `dataset.source is required` | Add missing field |

### API Errors

| Error | Message | Resolution |
|-------|---------|------------|
| Invalid HF token | `HuggingFace authentication failed` | Check HUGGINGFACE_TOKEN |
| Dataset not found | `Dataset 'x' not found or private` | Verify dataset name/access |
| DashScope error | `DashScope API error: {details}` | Check API key/quota |

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
flatfish/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── flatfish/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py                 # Typer CLI definitions
│       ├── config.py              # Config loading/validation
│       ├── dataset.py             # HuggingFace dataset handling
│       ├── htr/
│       │   ├── __init__.py
│       │   ├── engine.py          # HTR processing
│       │   └── models.py          # Model loading
│       ├── entities/
│       │   ├── __init__.py
│       │   ├── extractor.py       # Entity extraction
│       │   └── context.py         # Context generation
│       ├── summary/
│       │   ├── __init__.py
│       │   └── qwen.py            # DashScope/Qwen integration
│       ├── site/
│       │   ├── __init__.py
│       │   ├── builder.py         # Site generator
│       │   ├── search.py          # Pagefind integration
│       │   └── templates/
│       │       ├── base.html
│       │       ├── index.html
│       │       ├── main.html
│       │       ├── document.html
│       │       ├── browse_dates.html
│       │       └── browse_entities.html
│       └── utils/
│           ├── __init__.py
│           ├── images.py          # Image utilities
│           └── logging.py         # Logging setup
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_htr.py
    ├── test_entities.py
    ├── test_summary.py
    └── test_site.py
```

---

## Appendix

### A. Sample pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "flatfish"
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
    "python-dotenv>=1.0",
    "datasets>=2.0",
    "Pillow>=10.0",
    "transformers>=4.30",
    "torch>=2.0",
    "dashscope>=1.0",
    "jinja2>=3.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[project.scripts]
flatfish = "flatfish.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/flatfish"]
```

### B. Qwen-VL Model Options

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

*Last Updated: February 2026*
*Version: 0.1.0-spec*
