# HTR and OCR

Understand how Flatfish extracts text from handwritten and printed historical documents.

---

## What's the Difference?

### OCR (Optical Character Recognition)

- Designed for **printed text**
- Recognizes standard fonts
- Very accurate for typed documents
- Example tools: Tesseract, ABBYY

### HTR (Handwritten Text Recognition)

- Designed for **handwritten text**
- Learns to read different writing styles
- More challenging due to variation
- Example tools: Transkribus, Qwen-VL

Flatfish uses **Qwen-VL**, which handles both printed and handwritten text.

---

## How Qwen-VL Works

Qwen-VL is a **vision-language model** from Alibaba. It can:

1. **See** the image (vision component)
2. **Understand** what it sees (language component)
3. **Generate** text describing or transcribing the image

### Why Vision-Language Models?

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
│ 3. Post-Process │  Cleanup with custom prompt
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

### What Qwen-VL Handles Well

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

Tell the model what to expect:

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

Before uploading to Hugging Face:

1. **Crop** to document area (remove desk/background)
2. **Rotate** to correct orientation
3. **Adjust contrast** if faded
4. **Convert** to standard format (JPEG or PNG)

### Post-Processing Transcriptions

After extraction, manually correct:

1. **Names** - Proper nouns often need fixing
2. **Places** - Geographic names
3. **Numbers** - Dates and amounts
4. **Technical terms** - Domain-specific vocabulary

---

## Understanding Confidence Scores

Each transcription includes a confidence score (0-1):

```json
{
  "cleaned_text": "...",
  "confidence": 0.92
}
```

| Score | Meaning | Action |
|-------|---------|--------|
| 0.95+ | Very confident | Probably correct |
| 0.85-0.95 | Confident | Spot check |
| 0.70-0.85 | Uncertain | Review carefully |
| <0.70 | Low confidence | May need manual transcription |

### Finding Low-Confidence Documents

```bash
# List documents with confidence below 0.8
grep -l '"confidence": 0.[0-7]' transcriptions/*.json
```

---

## Comparison with Other Tools

### vs. Transkribus

| Feature | Flatfish (Qwen-VL) | Transkribus |
|---------|-------------------|-------------|
| Training required | No | Yes (for custom models) |
| Languages | Many | Many (with models) |
| Historical scripts | Good | Excellent |
| Cost | API usage | Subscription |
| Integration | Built-in | External tool |

### vs. Google Vision

| Feature | Flatfish (Qwen-VL) | Google Vision |
|---------|-------------------|---------------|
| Handwriting | Excellent | Good |
| Context understanding | Excellent | Limited |
| Historical documents | Good | Fair |
| Privacy | You control data | Google processes |

---

## Technical Details

### Model Specifications

- **Model**: Qwen-VL-Max
- **Input**: Images up to 4096x4096 pixels
- **Batch size**: 20 images per request
- **Languages**: English, Chinese, and many others
- **Context window**: ~32K tokens

### API Usage

Flatfish uses DashScope (Alibaba Cloud) API:

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

---

## Tips for Specific Document Types

### Diaries

- Usually single-hand writing
- May have abbreviations
- Often include dates in margins

```yaml
prompts:
  text_extraction: |
    This is a handwritten diary entry.
    Look for: date at top, margin notes, abbreviations.
    Preserve line breaks where they indicate new thoughts.
```

### Letters

- May have multiple hands (letter + envelope)
- Formal opening/closing conventions
- Often include dates and places

```yaml
prompts:
  text_extraction: |
    This is a handwritten letter.
    Look for: date, salutation, closing, signature.
    Note any postscripts or margin additions.
```

### Legal Documents

- Formal language and formatting
- Names and places are critical
- May include printed forms with handwriting

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
- **[AI Summarization](ai-summarization.md)** - Generating collection summaries
- **[Transcription Guide](../usage/transcription.md)** - Practical tips
