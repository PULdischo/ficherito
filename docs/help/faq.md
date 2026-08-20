# Frequently Asked Questions

Answers to common questions about Ficherito.

---

## General

### What is Ficherito?

Ficherito is a command-line tool that processes historical document images
into searchable, editable digital collections. It combines AI-powered
transcription (HTR/OCR), named entity recognition, and translation to turn
document images into structured data and a static, CMS-editable website.

### Who is Ficherito for?

- **Archivists** processing historical collections
- **Researchers** working with manuscript materials
- **Digital humanities** projects
- **Libraries and museums** digitizing collections
- **Genealogists** transcribing family documents

### Is Ficherito free?

Ficherito itself is open source and free. However:
- **API costs**: usage of your chosen LLM provider (e.g. DashScope/Qwen-VL) has associated costs
- **Hosting**: GitHub Pages is free; Netlify has a free tier

---

## Requirements

### What Python version do I need?

Python 3.10 or higher.

```bash
python --version
```

### Do I need Node.js?

Only for `ficherito build` (the website step) — it runs Eleventy and
Pagefind. The rest of the pipeline (`extract`, `entities`, `translate`)
doesn't need it.

### Do I need special hardware?

No. Ficherito runs on standard computers — processing happens via a cloud
API, no local GPU required. Works on Windows, macOS, and Linux.

---

## API Keys

### How do I get an API key?

By default Ficherito uses DashScope (Alibaba Cloud), hosting Qwen-VL:

1. Go to [dashscope.aliyun.com](https://dashscope.aliyun.com/)
2. Create an account (free tier available)
3. Generate an API key under **API Key Management**
4. Add it to `.env` as `OPENAI_API_KEY`

See the [Installation Guide](../getting-started/installation.md) for details.

### Can I use a different provider?

Yes — Ficherito talks to any **OpenAI-compatible** chat completions
endpoint with image input. Set `OPENAI_BASE_URL` and `OPENAI_MODEL` in
`.env` to point at OpenAI, a self-hosted model, or another provider.

### How much does the API cost?

Varies by provider and model. Check your provider's pricing page for
current per-request or per-token rates.

---

## Document Processing

### What image formats are supported?

JPEG, PNG, TIFF, WebP, HEIC, BMP, GIF, and PDF (rendered to page images
automatically).

### What image quality do I need?

300+ DPI recommended; documents work at lower resolution but with reduced
accuracy.

### How accurate is the transcription?

Depends heavily on image quality and handwriting clarity. Always review
transcriptions — they're editable Markdown files (or editable via the CMS
once deployed), not a final product.

### Can Ficherito read non-English documents?

Yes — the vision-language model handles many languages. Adjust
`prompts.text_extraction` to tell it what language/script to expect.

### Does it work with printed text or only handwriting?

Both — handwritten, typewritten, and printed documents, and mixed content.

---

## Entities

### What entity types does Ficherito recognize?

`PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `MONEY`, `LEGAL_TERM`,
`EVENT`, `DOCUMENT`, `OCCUPATION`, `RELATIONSHIP` by default — configurable
via the `ner_extraction` prompt. See [Entity Extraction](../usage/entities.md).

### Can I edit extracted entities?

Yes — edit the JSON files in `entities/` directly, or (once deployed)
through the Sveltia CMS at `/admin/`.

---

## Translation

### What translation service does Ficherito use?

Google Translate, via the `deep-translator` library. See [Translation](../usage/translation.md).

### Is translation part of the full pipeline?

No — `ficherito process` runs extract, entities, and build, but not
translate. Run `ficherito translate` explicitly, then rebuild.

---

## Website Building

### What kind of site does Ficherito create?

A static site built with [Eleventy](https://www.11ty.dev/): a password-gated
entry page, a full-text search page (Pagefind), individual document pages
with an image viewer and entities, and Browse by Date / Browse by Entity
pages.

### Can I customize the design?

Yes — edit the Nunjucks templates and CSS under `site/src/` directly (these
are yours to own; `ficherito build` only regenerates the emitted document
content, not your template edits). See [Building Sites](../usage/building-sites.md).

### Where can I host the site?

- **GitHub Pages** (recommended — free, and pairs with Sveltia CMS for
  browser-based editing)
- **Netlify** (built-in `ficherito deploy` command)
- Any static host, by uploading `site/_site/`

---

## Content Editing

### Can collaborators edit content without using git?

Yes — once deployed, the Sveltia CMS at `/admin/` lets people edit
transcriptions, translations, and entities through a form-based UI. Saves
commit directly to your GitHub repository and trigger a rebuild. See
[Deployment](../usage/deployment.md#editing-content-with-sveltia-cms).

---

## Workflow

### Can I resume interrupted processing?

Yes — `ficherito extract` and `ficherito entities` both skip documents that
already have output, so just re-run the same command.

### Can I reprocess a specific document?

```bash
rm transcriptions/document_001.md
ficherito extract
```

---

## Data & Privacy

### Where is my data processed?

- **Transcription, entity extraction, translation**: sent to your
  configured API provider (DashScope by default, or whichever you set)
- **Site building**: entirely local

### Can I process documents offline?

No — transcription, entity extraction, and translation all require API
access. Site building works offline once you have transcriptions.

---

## Future Plans

### How can I contribute?

- Report bugs on GitHub
- Suggest features
- Submit pull requests

---

## See Also

- **[Troubleshooting](troubleshooting.md)** - Problem solutions
- **[Glossary](glossary.md)** - Terms and definitions
- **[Getting Started](../getting-started/installation.md)** - Setup guide
