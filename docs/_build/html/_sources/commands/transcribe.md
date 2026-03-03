# flatfish transcribe

Extract text from document images using Qwen-VL vision-language model.

---

## Usage

```bash
flatfish transcribe [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `flatfish.yaml` |
| `--source` | `-s` | Image source directory | `images/` |
| `--output` | `-o` | Output directory | `transcriptions/` |
| `--batch-size` | `-b` | Images per API call | `20` |
| `--force` | `-f` | Reprocess existing | `False` |
| `--resume` | `-r` | Continue from last | `False` |
| `--file` | | Process single file | |
| `--verbose` | `-v` | Verbose output | `False` |

---

## What It Does

The `transcribe` command:

1. Reads document images (JPEG, PNG, TIFF)
2. Sends images to Qwen-VL for text extraction
3. Saves transcriptions as JSON files

```
images/
├── letter_001.jpg     → transcriptions/letter_001.json
├── letter_002.jpg     → transcriptions/letter_002.json
└── diary_page_001.jpg → transcriptions/diary_page_001.json
```

---

## Examples

### Transcribe All Images

```bash
flatfish transcribe
```

### Process Single File

```bash
flatfish transcribe --file images/letter_001.jpg
```

### Custom Source Directory

```bash
flatfish transcribe --source /path/to/scans/
```

### Resume Interrupted Run

```bash
flatfish transcribe --resume
```

### Force Reprocessing

```bash
flatfish transcribe --force
```

---

## Output Format

Each transcription is saved as JSON:

```json
{
  "source_file": "letter_001.jpg",
  "processed_at": "2024-01-15T10:30:00",
  "model": "qwen-vl-max",
  "raw_text": "Dear Brother,\n\nI write to inform you...",
  "cleaned_text": "Dear Brother,\n\nI write to inform you of our safe arrival in Philadelphia...",
  "confidence": 0.94,
  "metadata": {
    "image_width": 2400,
    "image_height": 3200,
    "processing_time_ms": 2340
  }
}
```

### Fields

| Field | Description |
|-------|-------------|
| `source_file` | Original image filename |
| `processed_at` | Timestamp of processing |
| `model` | AI model used |
| `raw_text` | Initial extraction |
| `cleaned_text` | Post-processed text |
| `confidence` | Model confidence (0-1) |
| `metadata` | Processing details |

---

## Configuration

### flatfish.yaml Settings

```yaml
transcription:
  # Images per API call (affects cost/speed)
  batch_size: 20
  
  # Minimum confidence to accept
  min_confidence: 0.5
  
  # Post-processing
  clean_text: true
  preserve_line_breaks: true

prompts:
  text_extraction: |
    Transcribe all handwritten and printed text in this image.
    
    Guidelines:
    - Preserve original spelling
    - Maintain paragraph structure
    - Note illegible sections as [illegible]
    - Expand common abbreviations in [brackets]
```

### Environment Variables

```bash
# Required: Qwen API key
DASHSCOPE_API_KEY=sk-your-key-here

# Optional: Hugging Face token for image source
HF_TOKEN=hf_your-token-here
```

---

## Progress Output

```
Flatfish Transcribe
═══════════════════

Found 500 images to process

Batch 1/25 (images 1-20)
  ✓ letter_001.jpg (conf: 0.95)
  ✓ letter_002.jpg (conf: 0.92)
  ...
  ✓ letter_020.jpg (conf: 0.88)

Batch 2/25 (images 21-40)
  ✓ letter_021.jpg (conf: 0.91)
  ...

═══════════════════
Complete: 500/500 images
Average confidence: 0.91
Low confidence (<0.7): 12 files
```

---

## Handling Low Confidence

### Find Low-Confidence Files

```bash
# List files with confidence < 0.7
grep -l '"confidence": 0\.[0-6]' transcriptions/*.json
```

### Review and Correct

1. Open the source image
2. Compare with transcription
3. Edit the JSON file manually
4. Or re-run with adjusted prompt

### Mark for Review

```json
{
  "cleaned_text": "...",
  "confidence": 0.62,
  "needs_review": true,
  "review_notes": "Faded ink, partial page"
}
```

---

## Image Preparation Tips

### Optimal Image Specifications

| Property | Recommendation |
|----------|----------------|
| Resolution | 300+ DPI |
| Format | JPEG or PNG |
| Color | Grayscale or color |
| Size | Under 4096x4096 px |
| File size | Under 20 MB |

### Pre-Processing

```bash
# Convert TIFF to JPEG
mogrify -format jpg *.tiff

# Resize oversized images
mogrify -resize '4096x4096>' *.jpg

# Increase contrast
mogrify -contrast-stretch 2%x1% *.jpg
```

---

## Custom Prompts

### For Specific Document Types

```yaml
# Diary entries
prompts:
  text_extraction: |
    This is a handwritten diary entry from the 1860s.
    
    Transcribe the text preserving:
    - Date headers (usually at top)
    - Paragraph breaks
    - Any margin notes
    
    Common abbreviations:
    - "thro" = through
    - "recd" = received
    - "&c" = etc.
```

```yaml
# Legal documents
prompts:
  text_extraction: |
    This is a legal document (deed, will, or court record).
    
    Pay special attention to:
    - Proper names of all parties
    - Dates and locations
    - Monetary amounts
    - Legal terminology
    
    Preserve exact wording for legal phrases.
```

### For Specific Languages

```yaml
# German documents
prompts:
  text_extraction: |
    Transcribe this German handwritten document.
    
    Note:
    - Preserve German spelling
    - Handle Fraktur/Gothic script
    - Common abbreviations: u. (und), d. (der)
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "API rate limit" | Too many requests | Wait and retry |
| "Image too large" | File > 20MB | Resize image |
| "Invalid image" | Corrupt file | Check image file |
| "API key invalid" | Wrong key | Check .env |

### Retry Failed Images

```bash
# List failed images
cat .flatfish/transcribe_errors.log

# Retry specific file
flatfish transcribe --file images/failed_image.jpg --force
```

---

## Batch Size Optimization

### Trade-offs

| Batch Size | Speed | Detail | Cost |
|------------|-------|--------|------|
| 5 | Slow | High | Higher |
| 20 (default) | Medium | Good | Medium |
| 50 | Fast | Lower | Lower |

### Adjust for Your Needs

```yaml
# High detail (important documents)
transcription:
  batch_size: 10

# Fast processing (large collection)
transcription:
  batch_size: 30
```

---

## See Also

- **[HTR and OCR](../concepts/htr-ocr.md)** - Understanding text extraction
- **[Processing Documents](../usage/processing-documents.md)** - Usage guide
- **[Configuration](../usage/configuration.md)** - Full configuration reference
