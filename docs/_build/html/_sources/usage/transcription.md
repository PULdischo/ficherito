# Transcription

Learn how Flatfish extracts and cleans text from historical document images.

---

## How Transcription Works

Flatfish uses Qwen-VL, a vision-language AI model, to read handwritten text from images. The process has two steps:

1. **Raw extraction** - The model reads the image and outputs text
2. **Cleaning** - A second AI pass cleans up errors and formats the text

```
┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ Document     │ ──▶ │ Qwen-VL reads │ ──▶ │ AI cleanup   │
│ Image        │     │ handwriting   │     │ & formatting │
└──────────────┘     └───────────────┘     └──────────────┘
```

---

## Understanding the Output

Each transcribed document produces a JSON file:

```json
{
  "id": "1863-04-15_page_001",
  "date": "1863-04-15",
  "filename": "1863-04-15_page_001.jpg",
  "raw_text": "April 15th 1863\nDear Sarah\nI write to you from...",
  "cleaned_text": "April 15th 1863\n\nDear Sarah,\n\nI write to you from camp near Fredericksburg...",
  "confidence": 0.92,
  "model": "qwen-vl-max",
  "processed_at": "2024-01-15T14:32:00Z"
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique identifier for the document |
| `date` | Extracted or provided date |
| `raw_text` | Unprocessed OCR output |
| `cleaned_text` | AI-cleaned transcription |
| `confidence` | Model's confidence score (0-1) |

---

## Customizing the Transcription Prompt

The default prompt works well for most English historical documents. Customize it for:

- Different languages
- Specific time periods
- Unusual handwriting styles
- Technical or specialized content

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
    
    Format the transcription to show:
    - Paragraph breaks where they appear
    - Signatures and marks
    - Any marginalia or insertions
    
    Raw OCR text:
    {raw_text}
    
    Cleaned transcription:
```

---

## Handling Common Issues

### Blurry or Damaged Documents

For documents with physical damage:

```yaml
prompts:
  text_extraction: |
    This document has some damage and faded areas.
    
    For unclear sections:
    - Use [?] for single illegible words
    - Use [illegible: ~5 words] for longer sections
    - Use [torn] or [stained] to note physical damage
    - Make best-effort guesses in [brackets?]
    
    Raw OCR text:
    {raw_text}
```

### Inconsistent Handwriting

When multiple people wrote in the same document:

```yaml
prompts:
  text_extraction: |
    This document contains text from multiple writers.
    When you detect a change in handwriting, note it as:
    [Hand 2 begins] or [Different writer]
    
    Raw OCR text:
    {raw_text}
```

### Documents with Tables or Forms

```yaml
prompts:
  text_extraction: |
    This is a historical form or ledger with tabular data.
    
    Preserve the table structure using markdown format:
    | Column 1 | Column 2 | Column 3 |
    |----------|----------|----------|
    | Data     | Data     | Data     |
    
    Raw OCR text:
    {raw_text}
```

---

## Editing Transcriptions

After processing, you can manually correct errors.

### Edit a Single Document

```bash
nano transcriptions/document_001.json
```

Find the `cleaned_text` field and make corrections:

```json
{
  "cleaned_text": "April 15th 1863\n\nDear Sarah,\n\nI corrected this text manually..."
}
```

### Bulk Editing

For systematic corrections across many documents:

```bash
# Find and replace across all transcriptions
find transcriptions/ -name "*.json" -exec \
  sed -i 's/tbe/the/g' {} \;
```

### Marking Manual Edits

Consider adding a field to track manual edits:

```json
{
  "cleaned_text": "...",
  "manually_edited": true,
  "edited_at": "2024-01-16",
  "editor_notes": "Corrected place names based on context"
}
```

---

## Quality Control

### Review Low-Confidence Transcriptions

Find documents with low confidence scores:

```bash
# List documents with confidence below 0.8
grep -l '"confidence": 0.[0-7]' transcriptions/*.json
```

### Spot-Check Random Documents

```bash
# View a random transcription
cat $(ls transcriptions/*.json | shuf -n 1) | jq '.cleaned_text'
```

### Compare Raw vs Cleaned

```bash
# See what the AI changed
cat transcriptions/document_001.json | jq '{raw: .raw_text, cleaned: .cleaned_text}'
```

---

## Transcription Statistics

After processing, get an overview:

```bash
flatfish status --transcriptions
```

```
Transcription Statistics
════════════════════════

Total documents: 500
Completed: 487 (97.4%)
Failed: 3 (0.6%)
Skipped: 10 (2.0%)

Average confidence: 0.89
Low confidence (<0.8): 42 documents

Total words: 145,230
Average words per document: 298

Processing time: 1h 23m
Average per document: 10.2 seconds
```

---

## Exporting Transcriptions

### Export as Plain Text

```bash
# All transcriptions in one file
for f in transcriptions/*.json; do
  jq -r '.cleaned_text' "$f"
  echo -e "\n---\n"
done > all_transcriptions.txt
```

### Export as CSV

```bash
# Create CSV with id, date, and text
echo "id,date,text" > transcriptions.csv
for f in transcriptions/*.json; do
  jq -r '[.id, .date, .cleaned_text | gsub("\n"; " ")] | @csv' "$f" >> transcriptions.csv
done
```

### Export as TEI XML

For scholarly editing projects, consider converting to TEI format (this requires additional tools).

---

## Next Steps

- **[Entity Extraction](entities.md)** - Extract people, places, and dates
- **[Summarization](summarization.md)** - Generate AI summaries
- **[Building Sites](building-sites.md)** - Create your website
