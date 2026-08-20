# HTR and OCR

Understand how Ficherito extracts text from handwritten and printed historical documents.

---

## What's the Difference?

### OCR (Optical Character Recognition)

- Designed for **printed text**
- Recognizes standard fonts
- Very accurate for typed documents

### HTR (Handwritten Text Recognition)

- Designed for **handwritten text**
- Learns to read different writing styles
- More challenging due to variation

Ficherito uses a **vision-language model** (Qwen-VL by default, via
DashScope), which handles both printed and handwritten text in a single
pass.

---

## Why Vision-Language Models?

Traditional OCR/HTR uses pattern matching. Vision-language models understand **context**:

```
Traditional OCR:  "tbe" → outputs "tbe" (doesn't know it's wrong)

Vision-Language:  "tbe" → outputs "the" (understands context)
```

---

## The Transcription Process

```
┌─────────────────┐
│ Document Image  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. Vision       │  Model "sees" the handwriting
│    Encoder      │  Extracts visual features
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Language     │  Generates text from features
│    Decoder      │  Uses context to resolve ambiguity
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Post-Process │  Cleanup with the `text_extraction` prompt
│    Cleaning     │  Preserves historical spelling
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Final           │
│ Transcription   │
└─────────────────┘
```

---

## Factors Affecting Accuracy

### Image Quality

| Factor | Impact | Recommendation |
|--------|--------|----------------|
| Resolution | High | 300+ DPI for best results |
| Contrast | High | Dark ink on light paper |
| Lighting | Medium | Even, no shadows |
| Focus | High | Sharp, not blurry |
| Color | Low | Grayscale usually fine |

### Document Characteristics

| Factor | Impact | Notes |
|--------|--------|-------|
| Handwriting clarity | Very High | Neat writing > messy |
| Language | High | English best, others vary |
| Time period | Medium | Older scripts harder |
| Ink condition | Medium | Faded ink harder |
| Paper condition | Medium | Damage reduces accuracy |

### What Vision-Language Models Handle Well

- ✅ Cursive handwriting
- ✅ Mixed print and handwriting
- ✅ Multiple columns
- ✅ Marginalia and annotations
- ✅ Various languages

### Challenging Cases

- ⚠️ Very faded documents
- ⚠️ Heavy damage or staining
- ⚠️ Unusual scripts (Gothic, etc.)
- ⚠️ Technical notation (math, music)
- ⚠️ Cross-hatched writing

---

## Improving Transcription Quality

### Custom Prompts

Tell the model what to expect via `prompts.text_extraction` in `ficherito.yaml`:

```yaml
prompts:
  text_extraction: |
    This is a 19th-century American diary written in English.
    The writer uses common abbreviations:
    - "thro" = through
    - "recd" = received
    - "&c" = etc.

    Preserve original spelling but expand abbreviations in [brackets].

    Raw OCR text:
    {raw_text}
```

### Pre-Processing Images

Before processing:

1. **Crop** to document area (remove desk/background)
2. **Rotate** to correct orientation
3. **Adjust contrast** if faded
4. **Convert** to a standard format (JPEG or PNG) — or leave PDFs as-is, Ficherito renders them to page images automatically

### Post-Processing Transcriptions

After extraction, manually correct:

1. **Names** - Proper nouns often need fixing
2. **Places** - Geographic names
3. **Numbers** - Dates and amounts
4. **Technical terms** - Domain-specific vocabulary

---

## Understanding Confidence Scores

When the model reports one, a confidence score (0-1) is stored in the
transcription file's frontmatter:

```markdown
---
title: document_001
extracted_at: '2026-01-15T10:30:00Z'
model: qwen-vl-max
confidence: 0.92
---

Transcribed text here...
```

| Score | Meaning | Action |
|-------|---------|--------|
| 0.95+ | Very confident | Probably correct |
| 0.85-0.95 | Confident | Spot check |
| 0.70-0.85 | Uncertain | Review carefully |
| <0.70 | Low confidence | May need manual transcription |

### Finding Low-Confidence Documents

```bash
grep -l "confidence: 0.[0-6]" transcriptions/*.md
```

---

## Technical Details

### API Usage

Ficherito talks to any **OpenAI-compatible** chat completions endpoint with
image input — configured via `OPENAI_BASE_URL` / `OPENAI_API_KEY` /
`OPENAI_MODEL` in `.env`. The default is DashScope (Alibaba Cloud), hosting
Qwen-VL:

```python
# Under the hood
response = client.chat.completions.create(
    model="qwen-vl-max",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": image_base64}},
            {"type": "text", "text": "Transcribe this document..."}
        ]
    }]
)
```

Swapping providers (OpenAI, a self-hosted model, etc.) is just a matter of
changing `OPENAI_BASE_URL` and `OPENAI_MODEL` — no code changes needed.

---

## Tips for Specific Document Types

### Diaries

```yaml
prompts:
  text_extraction: |
    This is a handwritten diary entry.
    Look for: date at top, margin notes, abbreviations.
    Preserve line breaks where they indicate new thoughts.
```

### Letters

```yaml
prompts:
  text_extraction: |
    This is a handwritten letter.
    Look for: date, salutation, closing, signature.
    Note any postscripts or margin additions.
```

### Legal Documents

```yaml
prompts:
  text_extraction: |
    This is a legal document (deed, will, or court record).
    Pay special attention to proper names, dates, and amounts.
    Preserve exact wording of legal phrases.
```

---

## Next Steps

- **[Named Entities](named-entities.md)** - Extracting people, places, dates
- **[Transcription Guide](../usage/transcription.md)** - Practical tips
