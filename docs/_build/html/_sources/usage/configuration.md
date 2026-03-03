# Configuration

This guide covers all configuration options for Flatfish projects.

---

## Configuration Files

Flatfish uses two configuration files:

| File | Purpose | Version Control |
|------|---------|-----------------|
| `flatfish.yaml` | Project settings | ✅ Commit to Git |
| `.env` | API keys and secrets | ❌ Never commit |

---

## flatfish.yaml Reference

Here's a complete configuration file with all options:

```yaml
# =============================================================================
# DATASET CONFIGURATION
# =============================================================================
dataset:
  # Hugging Face dataset identifier (required)
  # Format: "username/dataset-name" or "organization/dataset-name"
  source: "PULdischo/marshall-diaries"
  
  # Which splits to process (default: ["train"])
  # Common splits: train, test, validation
  splits:
    - "train"
  
  # Column containing document images (required)
  image_column: "image"
  
  # Column containing document dates (optional)
  # If provided, documents will be sorted chronologically
  date_column: "date"
  
  # Column containing document IDs (optional)
  # If not provided, filenames or indices will be used
  id_column: "id"

# =============================================================================
# PROCESSING OPTIONS
# =============================================================================
processing:
  # Whether to extract named entities after transcription
  extract_entities: true
  
  # Include contextual descriptions for entities
  # e.g., "Person; the plaintiff in the legal case" instead of just "Person"
  entity_context: true
  
  # Save intermediate results (useful for debugging)
  save_intermediate: true
  
  # Number of concurrent API requests (be careful with rate limits)
  concurrency: 3

# =============================================================================
# CUSTOM PROMPTS
# =============================================================================
prompts:
  # Prompt for cleaning up raw OCR text
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

  # Prompt for document summarization
  # Available variable: {documents}
  summary: |
    You are a historian analyzing a sequence of related documents...

# =============================================================================
# SUMMARY OPTIONS
# =============================================================================
summary:
  # Enable/disable summary generation
  enabled: true
  
  # Model to use for summarization
  # Options: qwen-vl-max, qwen-vl-plus
  model: "qwen-vl-max"
  
  # Maximum documents to include in summary
  # For large collections, this samples evenly across the date range
  sample_size: 100

# =============================================================================
# WEBSITE OPTIONS
# =============================================================================
website:
  # Site title (appears in header and browser tab)
  title: "Document Collection"
  
  # Site description (for SEO and overview page)
  description: "A collection of historical documents"
  
  # Password protection (leave empty for public access)
  password: ""
  
  # Custom CSS file (optional)
  custom_css: ""
  
  # Google Analytics ID (optional)
  analytics_id: ""
  
  # Show/hide specific sections
  show_timeline: true
  show_entities: true
  show_summary: true

# =============================================================================
# OUTPUT DIRECTORIES
# =============================================================================
output:
  # Where to save transcriptions
  transcriptions_dir: "transcriptions"
  
  # Where to save entity extractions
  entities_dir: "entities"
  
  # Where to save summaries
  summaries_dir: "summaries"
  
  # Where to build the static site
  site_dir: "_site"
  
  # Where to save downloaded images (optional)
  images_dir: "images"
```

---

## Environment Variables (.env)

The `.env` file contains sensitive API keys:

```bash
# Hugging Face token for dataset access
# Get yours at: https://huggingface.co/settings/tokens
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# DashScope API key for Qwen models
# Get yours at: https://dashscope.aliyun.com/
DASHSCOPE_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Netlify token for deployment (optional)
# Get yours at: https://app.netlify.com/user/applications
NETLIFY_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Netlify site ID for deployment (optional)
NETLIFY_SITE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

```{warning}
**Never commit `.env` to version control!** It contains secrets that could be misused if exposed.
```

---

## Configuration Precedence

Settings are loaded in this order (later overrides earlier):

1. Default values (built into Flatfish)
2. `flatfish.yaml` in current directory
3. Environment variables
4. Command-line options

For example:
```bash
# This overrides the config file's output directory
flatfish build --output ./my-custom-site
```

---

## Validating Configuration

Always validate your configuration before processing:

```bash
flatfish validate
```

This checks:

- ✅ Configuration file syntax
- ✅ Required fields present
- ✅ API keys configured
- ✅ Dataset accessible
- ✅ Output directories writable

---

## Per-Document Configuration

For documents that need special handling, you can create per-document override files:

```
transcriptions/
├── document_001.json
├── document_001.override.yaml  # Override settings for this document
├── document_002.json
└── ...
```

Override file example:
```yaml
# document_001.override.yaml
skip_entity_extraction: true
custom_prompt: |
  This document is in French. Transcribe it...
```

---

## Examples

### Minimal Configuration

```yaml
dataset:
  source: "my-username/my-dataset"
  image_column: "image"
```

### Academic Research Project

```yaml
dataset:
  source: "university-archive/civil-war-letters"
  splits: ["train", "test"]
  image_column: "scan"
  date_column: "letter_date"

processing:
  extract_entities: true
  entity_context: true

summary:
  enabled: true
  sample_size: 200

website:
  title: "Smith Family Civil War Correspondence"
  description: "Letters from the Smith family, 1861-1865"
  password: "research2024"
```

### Public Digital Collection

```yaml
dataset:
  source: "library/historic-newspapers"
  image_column: "page_image"

processing:
  extract_entities: true

website:
  title: "Historic Newspaper Archive"
  description: "Digitized newspapers from 1850-1920"
  password: ""  # Public access
  analytics_id: "G-XXXXXXXXXX"
```

---

## Next Steps

- **[Processing Documents](processing-documents.md)** - Learn about the processing pipeline
- **[Custom Prompts](transcription.md)** - Fine-tune text extraction
- **[Troubleshooting](../help/troubleshooting.md)** - Solve common issues
