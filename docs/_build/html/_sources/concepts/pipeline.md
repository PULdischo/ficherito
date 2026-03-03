# The Processing Pipeline

Understand how Flatfish transforms document images into a searchable website.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLATFISH PIPELINE                            │
└─────────────────────────────────────────────────────────────────┘

     ┌─────────────┐
     │ HuggingFace │
     │   Dataset   │
     └──────┬──────┘
            │
            ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  1. EXTRACTION    │     │ • Download images                   │
│                   │ ──▶ │ • Send to Qwen-VL for OCR           │
│  flatfish extract │     │ • Clean and format transcriptions   │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  2. ENTITIES      │     │ • Analyze transcriptions            │
│                   │ ──▶ │ • Identify people, places, dates    │
│  flatfish entities│     │ • Add contextual descriptions       │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  3. SUMMARIZE     │     │ • Process documents in batches      │
│                   │ ──▶ │ • Generate timeline & changes       │
│flatfish summarize │     │ • Create finding aid & questions    │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
┌───────────────────┐     ┌─────────────────────────────────────┐
│  4. BUILD         │     │ • Generate HTML pages               │
│                   │ ──▶ │ • Create search index               │
│  flatfish build   │     │ • Output static website             │
└─────────┬─────────┘     └─────────────────────────────────────┘
          │
          ▼
     ┌─────────────┐
     │   Static    │
     │   Website   │
     └─────────────┘
```

---

## Stage 1: Extraction

**Purpose:** Convert document images to text.

**Input:** Images from Hugging Face dataset  
**Output:** JSON files in `transcriptions/`

### Process

1. **Download** images from your configured dataset
2. **Send** each image to Qwen-VL (vision-language model)
3. **Extract** raw text using HTR/OCR
4. **Clean** text using AI post-processing
5. **Save** as JSON with metadata

### Output Format

```json
{
  "id": "1863-04-15_001",
  "date": "1863-04-15",
  "filename": "1863-04-15_001.jpg",
  "raw_text": "April 15th 1863...",
  "cleaned_text": "April 15th, 1863\n\nDear Sarah...",
  "confidence": 0.92,
  "model": "qwen-vl-max",
  "processed_at": "2024-01-15T14:32:00Z"
}
```

---

## Stage 2: Entity Extraction

**Purpose:** Identify named entities with context.

**Input:** Transcription files  
**Output:** JSON files in `entities/`

### Process

1. **Read** cleaned transcription text
2. **Analyze** with AI to find entities
3. **Classify** each entity by type
4. **Generate** contextual descriptions
5. **Save** as JSON

### Output Format

```json
{
  "document_id": "1863-04-15_001",
  "entities": [
    {
      "text": "Sarah",
      "type": "PERSON",
      "context": "Person; the recipient of the letter, likely the writer's wife"
    },
    {
      "text": "Philadelphia",
      "type": "LOCATION",
      "context": "Location; city mentioned as destination"
    }
  ]
}
```

---

## Stage 3: Summarization

**Purpose:** Generate collection-level analysis.

**Input:** All transcription files  
**Output:** Summary files in `summaries/`

### Process

1. **Sort** documents by date
2. **Batch** into groups of 20 images
3. **Process** each batch with 4 parallel tracks:
   - Timeline events
   - Key changes
   - Research questions
   - Narrative summary
4. **Combine** results hierarchically
5. **Save** to editable text files

### Track-Based Processing

```
Batch 1 ──┬──▶ Timeline      ──┐
          ├──▶ Key Changes   ──┼──▶ Combine ──▶ Final Timeline
          ├──▶ Questions     ──┤
          └──▶ Narrative     ──┘

Batch 2 ──┬──▶ Timeline      ──┐
          ├──▶ Key Changes   ──┼──▶ Combine ──▶ Final Changes
          ├──▶ Questions     ──┤
          └──▶ Narrative     ──┘

...
```

---

## Stage 4: Build

**Purpose:** Create static website.

**Input:** All processed files  
**Output:** HTML/CSS/JS in `_site/`

### Process

1. **Load** transcriptions, entities, summaries
2. **Generate** document pages (one per document)
3. **Generate** entity index
4. **Generate** overview pages (summary, timeline, etc.)
5. **Create** search index with Pagefind
6. **Copy** images and assets

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        INPUT                                 │
├──────────────────────────────────────────────────────────────┤
│  HuggingFace Dataset                                         │
│  ├── image_001.jpg                                           │
│  ├── image_002.jpg                                           │
│  └── ...                                                     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    INTERMEDIATE FILES                        │
├──────────────────────────────────────────────────────────────┤
│  transcriptions/           entities/           summaries/    │
│  ├── doc_001.json         ├── doc_001.json    ├── timeline   │
│  ├── doc_002.json         ├── doc_002.json    ├── changes    │
│  └── ...                  └── ...             └── questions  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        OUTPUT                                │
├──────────────────────────────────────────────────────────────┤
│  _site/                                                      │
│  ├── index.html                                              │
│  ├── main.html                                               │
│  ├── overview/                                               │
│  ├── entities/                                               │
│  ├── pagefind/                                               │
│  └── images/                                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Running Pipeline Stages

### Full Pipeline

```bash
flatfish process
```

### Individual Stages

```bash
flatfish extract      # Stage 1 only
flatfish entities     # Stage 2 only
flatfish summarize    # Stage 3 only
flatfish build        # Stage 4 only
```

### Dependencies

| Stage | Requires |
|-------|----------|
| Extract | Dataset access |
| Entities | Transcriptions |
| Summarize | Transcriptions |
| Build | Transcriptions (entities/summaries optional) |

---

## Resume Capability

Each stage saves its output immediately. If processing is interrupted:

```bash
# Just run the same command again
flatfish extract

# Already-processed files are skipped
Extracting text from 500 documents...
  [1-450] Already processed, skipping...
  [451/500] Processing...
```

---

## Next Steps

- **[HTR and OCR](htr-ocr.md)** - How text extraction works
- **[Named Entities](named-entities.md)** - Understanding entity extraction
- **[AI Summarization](ai-summarization.md)** - How summaries are generated
