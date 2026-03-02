# Frequently Asked Questions

Answers to common questions about Flatfish.

---

## General

### What is Flatfish?

Flatfish is a command-line tool that processes historical document images to create searchable, accessible digital collections. It combines AI-powered transcription (HTR/OCR), named entity recognition, and summarization to transform document images into structured data and static websites.

### Who is Flatfish for?

- **Archivists** processing historical collections
- **Researchers** working with manuscript materials
- **Digital humanities** projects
- **Libraries and museums** digitizing collections
- **Genealogists** transcribing family documents

### Is Flatfish free?

Flatfish itself is open source and free. However:
- **API costs**: Qwen-VL API usage has associated costs
- **Hosting**: Optional deployment may have costs (free tiers available)

---

## Requirements

### What Python version do I need?

Python 3.9 or higher. We recommend Python 3.11.

```bash
python --version
# Should show 3.9+
```

### Do I need special hardware?

No. Flatfish runs on standard computers:
- Processing happens via cloud APIs
- No GPU required locally
- Works on Windows, macOS, and Linux

### How much disk space is needed?

Depends on your collection:
- Flatfish installation: ~500 MB (including spaCy models)
- Per document: ~50 KB (transcription + entities + metadata)
- Website: Varies with images

---

## API Keys

### How do I get a Qwen API key?

1. Go to [Alibaba Cloud Console](https://www.alibabacloud.com/)
2. Create an account (free tier available)
3. Navigate to DashScope
4. Generate API key
5. Add to `.env` file

See [Installation Guide](../getting-started/installation.md) for details.

### How much does the API cost?

Pricing varies. Approximate costs:
- Qwen-VL: ~$0.002-0.01 per image
- 500 documents: ~$5-10

Check [DashScope pricing](https://www.alibabacloud.com/product/dashscope) for current rates.

### Can I use my own API/model?

Currently Flatfish is optimized for Qwen-VL. Future versions may support:
- Azure OpenAI
- Google Gemini
- Local models

---

## Document Processing

### What image formats are supported?

- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- WebP (.webp)

### What image quality do I need?

- **Minimum**: 200 DPI
- **Recommended**: 300 DPI
- **Maximum dimensions**: 4096 x 4096 pixels
- **Maximum file size**: 20 MB

### How accurate is the transcription?

Accuracy depends on:
- Image quality: 90%+ for clear documents
- Handwriting clarity: 80-95% for neat writing
- Historical scripts: 70-90% (varies significantly)

Always review AI transcriptions for accuracy.

### Can Flatfish read non-English documents?

Yes! Qwen-VL supports many languages:
- English
- German
- French
- Spanish
- Chinese
- And more

Configure with custom prompts:
```yaml
prompts:
  text_extraction: |
    This document is written in German...
```

### Does it work with printed text or only handwriting?

Both! Qwen-VL handles:
- Handwritten documents
- Typewritten documents
- Printed books/newspapers
- Mixed content

---

## Summarization

### What are "tracks" in summarization?

Flatfish uses four specialized analysis tracks:

1. **Timeline** - Chronological events
2. **Key Changes** - Evolving themes
3. **Research Questions** - Investigation suggestions
4. **Narrative** - Prose summary

See [Track Summarization](../concepts/track-summarization.md) for details.

### Why hierarchical combining?

Large collections (300+ batches) can't fit in one API call. Hierarchical combining processes in groups:

```
337 batches → 7 intermediates → 1 final summary
```

See [Hierarchical Combining](../concepts/hierarchical-combining.md).

### Can I edit the AI-generated summaries?

Yes! Summaries are saved as plain text files:
```
output/
├── timeline.txt
├── key_changes.txt
├── research_questions.txt
└── finding_aid.txt
```

Edit with any text editor.

---

## Entities

### What entities does Flatfish recognize?

Default entity types:
- **PERSON** - People
- **GPE** - Places (cities, countries)
- **DATE** - Dates and times
- **ORG** - Organizations
- **LOC** - Locations (rivers, mountains)
- **MONEY** - Monetary values

### Can I add custom entities?

Yes:
```yaml
entities:
  custom_persons:
    - "John Smith"
    - "Mary Williams"
  custom_places:
    - "Smith Farm"
```

### How do I normalize entity variations?

Map variations to canonical forms:
```yaml
entities:
  normalization:
    "Jno. Smith": "John Smith"
    "J. Smith": "John Smith"
```

---

## Website Building

### What kind of site does Flatfish create?

A static HTML site with:
- Home page
- Finding aid/summary
- Document viewer pages
- Entity browser
- Search functionality
- Timeline view

### Can I customize the design?

Yes:
1. Use built-in themes
2. Add custom CSS
3. Create custom templates

See [Building Sites](../usage/building-sites.md).

### Where can I host the site?

Flatfish supports:
- **Netlify** (recommended)
- **GitHub Pages** (free)
- **Vercel**
- **Cloudflare Pages**
- Any static hosting

---

## Workflow

### How long does processing take?

Approximate times for 500 documents:
- Transcription: 1-2 hours
- Entities: 5-10 minutes
- Summarization: 30-60 minutes
- Combining: 5 minutes
- Building: 1-2 minutes

### Can I resume interrupted processing?

Yes:
```bash
flatfish process --resume
```

Progress is saved automatically.

### Can I reprocess specific documents?

Yes:
```bash
# Single file
flatfish transcribe --file images/letter_001.jpg --force

# All files
flatfish transcribe --force
```

---

## Data & Privacy

### Where is my data processed?

- **Transcription/Summarization**: Alibaba Cloud (Qwen API)
- **Entity extraction**: Locally (spaCy)
- **Site building**: Locally

### Is my data stored by the API provider?

Check Alibaba Cloud's data retention policy. For sensitive documents, consider:
- Redacting identifying information
- Using private/enterprise API tiers
- Waiting for local model support

### Can I process documents offline?

Currently, transcription and summarization require API access. Entity extraction and site building work offline.

---

## Comparison

### How does Flatfish compare to Transkribus?

| Feature | Flatfish | Transkribus |
|---------|----------|-------------|
| Training required | No | Yes (for custom) |
| Integrated pipeline | Yes | Partial |
| Static site output | Yes | No |
| Cost model | Per-use API | Subscription |
| Entity extraction | Built-in | Add-on |

### How does it compare to Google Document AI?

| Feature | Flatfish | Google Document AI |
|---------|----------|-------------------|
| Historical focus | Yes | General |
| Handwriting | Excellent | Good |
| Summarization | Built-in | Separate service |
| Open source | Yes | No |

---

## Future Plans

### What features are planned?

- Additional AI model support (GPT-4V, Gemini)
- Local model option (for offline/privacy)
- Collaborative editing
- Enhanced visualizations
- Multi-collection support

### How can I contribute?

- Report bugs on GitHub
- Suggest features
- Submit pull requests
- Share use cases

---

## See Also

- **[Troubleshooting](troubleshooting.md)** - Problem solutions
- **[Glossary](glossary.md)** - Terms and definitions
- **[Getting Started](../getting-started/installation.md)** - Setup guide
