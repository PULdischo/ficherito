# Processing Documents

Learn how to process document collections efficiently, handle large datasets, and troubleshoot common issues.

---

## The Processing Pipeline

When you run `flatfish process`, several stages happen in sequence:

```
┌─────────────────┐
│  1. Download    │  Fetch images from Hugging Face
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Extract     │  OCR/HTR to get raw text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Clean       │  AI cleanup of transcription
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Entities    │  Extract people, places, dates
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. Summarize   │  Generate timeline & analysis
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. Build       │  Create static website
└─────────────────┘
```

---

## Running the Full Pipeline

Process everything with one command:

```bash
flatfish process
```

This is equivalent to running each stage separately:

```bash
flatfish extract
flatfish entities
flatfish summarize
flatfish build
```

---

## Running Individual Stages

### Extract Text Only

```bash
flatfish extract
```

**What it does:**
- Downloads images from your Hugging Face dataset
- Sends each image to the Qwen-VL model for text extraction
- Cleans up the raw OCR output using your prompt
- Saves results to `transcriptions/`

**When to use:**
- You only need transcriptions, not entities or summaries
- You want to review transcriptions before proceeding

### Extract Entities Only

```bash
flatfish entities
```

**What it does:**
- Reads transcriptions from `transcriptions/`
- Identifies named entities (people, places, dates, etc.)
- Adds contextual descriptions
- Saves results to `entities/`

**Prerequisites:**
- Must run `flatfish extract` first

### Generate Summary Only

```bash
flatfish summarize
```

**What it does:**
- Reads transcriptions and sorts by date
- Processes documents in batches (20 images per batch)
- Generates timeline, key changes, and research questions
- Saves results to `summaries/`

**Prerequisites:**
- Must run `flatfish extract` first

### Build Website Only

```bash
flatfish build
```

**What it does:**
- Reads transcriptions, entities, and summaries
- Generates HTML pages for each document
- Creates entity index and search index
- Outputs to `_site/`

**Prerequisites:**
- Must run `flatfish extract` first
- Entities and summaries are optional

---

## Working with Large Collections

### Understanding Batch Processing

For collections with more than 20 documents, Flatfish processes them in batches. This is necessary because:

1. **AI model limits** - Qwen-VL can only process ~20 images per request
2. **Memory management** - Processing thousands of images at once would crash
3. **Resume capability** - If processing fails, you can resume from where you left off

### Resuming Interrupted Processing

If processing stops (network error, timeout, etc.), simply run the same command again:

```bash
flatfish extract
```

Flatfish automatically:
- Detects which documents are already processed
- Skips completed documents
- Continues from where it left off

### Monitoring Progress

Watch the terminal for progress updates:

```
Extracting text from 500 documents...
  [125/500] document_125.jpg ✓ (25% complete)
  Estimated time remaining: 45 minutes
```

### Setting Sample Size for Testing

For large collections, test with a subset first:

```yaml
# In flatfish.yaml
summary:
  sample_size: 50  # Only use 50 documents for summary
```

Or use command-line options:

```bash
flatfish extract --limit 20  # Only process first 20 documents
```

---

## Performance Tips

### Optimize for Speed

```yaml
processing:
  concurrency: 5  # Process 5 documents at once (default: 3)
```

```{warning}
Higher concurrency may hit API rate limits. Start with 3 and increase gradually.
```

### Optimize for Cost

```yaml
summary:
  model: "qwen-vl-plus"  # Cheaper than qwen-vl-max
  sample_size: 100       # Limit documents in summary
```

### Estimate Processing Time

Rough estimates per document:
- Text extraction: 5-15 seconds
- Entity extraction: 3-8 seconds
- Summary generation: 10-30 seconds per batch

For a 500-document collection:
- Text extraction: ~45-90 minutes
- Entities: ~30-60 minutes
- Summary: ~15-30 minutes

---

## Handling Errors

### Common Errors

**API Rate Limits**
```
Error: Rate limit exceeded. Retrying in 60 seconds...
```

Flatfish automatically retries with backoff. If it persists, reduce concurrency.

**Timeout Errors**
```
Error: Request timed out for document_123.jpg
```

The document may be too large or complex. It will be skipped and noted.

**Invalid Images**
```
Error: Cannot process document_456.jpg - invalid image format
```

Check that the file is a valid image (JPEG, PNG, TIFF).

### Viewing Error Logs

Check the detailed log file:

```bash
cat flatfish.log
```

Or increase verbosity:

```bash
flatfish process --verbose
```

### Skipping Problematic Documents

Create a `.flatfishignore` file:

```
# Skip these files
document_corrupted.jpg
batch_2023/*_draft.jpg
```

---

## Checking Processing Status

See what's been processed:

```bash
flatfish status
```

Output:
```
Processing Status
═══════════════════════════════════════

Dataset: PULdischo/marshall-diaries
Total documents: 500

Transcriptions:  450/500 (90%)  ▓▓▓▓▓▓▓▓▓░
Entities:        450/500 (90%)  ▓▓▓▓▓▓▓▓▓░
Summary:         ✓ Generated

Last processed: 2024-01-15 14:32:00
```

---

## Reprocessing Documents

### Reprocess Everything

```bash
# Delete all outputs
rm -rf transcriptions/ entities/ summaries/

# Process again
flatfish process
```

### Reprocess Specific Documents

Delete the specific output files:

```bash
rm transcriptions/document_123.json
rm entities/document_123.json

flatfish extract
flatfish entities
```

### Regenerate Summary Only

```bash
rm -rf summaries/
flatfish summarize
```

### Regenerate Summary Combination Only

If batch files exist but combining failed:

```bash
flatfish combine
```

---

## Processing Different Document Types

### Handwritten Documents

Default settings work well. Consider customizing the prompt for specific handwriting styles:

```yaml
prompts:
  text_extraction: |
    This is a 19th-century American handwritten letter.
    The writer uses common abbreviations of the period...
```

### Printed Historical Documents

Printed text is usually cleaner:

```yaml
prompts:
  text_extraction: |
    This is a printed document from the early 20th century.
    Focus on preserving formatting and column structure...
```

### Mixed Collections

For collections with different document types, consider:

1. Processing in separate batches
2. Using different prompts for each type
3. Creating multiple Flatfish projects

---

## Next Steps

- **[Transcription Details](transcription.md)** - Fine-tune text extraction
- **[Entity Extraction](entities.md)** - Customize entity recognition
- **[Summarization](summarization.md)** - Configure AI summaries
