# Glossary

Definitions of terms used in Ficherito documentation.

---

## A

### API (Application Programming Interface)
A way for software programs to communicate. Ficherito uses an API to send document images to a vision-language model and receive transcriptions.

### API Key
A secret code that identifies you to an API service. Required for your configured LLM provider (`OPENAI_API_KEY`).

---

## C

### CLI (Command Line Interface)
A text-based way to interact with software. Ficherito uses CLI commands like `ficherito process` instead of a graphical interface.

### Confidence Score
A number (0-1) indicating how certain the model is about a transcription, stored in the transcription file's frontmatter when the provider reports one.

### Consolidated Entities
`entities/consolidated.json` — all extracted entities grouped by type and text, with mention counts and per-document contexts across the whole collection. Powers the site's Browse by Entity page.

---

## D

### DashScope
Alibaba Cloud's AI service platform, and Ficherito's default LLM provider. Hosts the Qwen-VL model.

### DPI (Dots Per Inch)
A measure of image resolution. 300 DPI is a good target for scanned documents.

---

## E

### Eleventy (11ty)
The static site generator Ficherito's website is built with. See [Building Sites](../usage/building-sites.md).

### Entity
A named item in text — a person, place, date, organization, etc. See [Named Entities](../concepts/named-entities.md).

### Entity Context
A short description explaining an entity's role in a specific document, e.g. "Person; the plaintiff filing the complaint" rather than just "Person".

---

## F

### Ficherito
This tool! A CLI for processing historical documents with AI and building an editable static website.

### Frontmatter
YAML metadata at the top of a Markdown file, delimited by `---` lines. Used in transcription files (model, confidence, timestamp) and in the emitted site content (date, entities, prev/next navigation).

---

## H

### HTR (Handwritten Text Recognition)
The process of converting handwritten document images to digital text. More challenging than OCR due to handwriting variation.

---

## M

### Markdown
A simple text formatting language. Ficherito stores transcriptions, translations, and site content as Markdown files (`.md`).

### Model
An AI system trained to perform a task. Ficherito uses a vision-language model (Qwen-VL by default) for both transcription and entity extraction.

---

## N

### Named Entity Recognition (NER)
The process of identifying and categorizing named items (entities) in text. See [Named Entities](../concepts/named-entities.md).

---

## O

### OCR (Optical Character Recognition)
The process of converting printed text images to digital text. Ficherito's vision-language model handles both OCR and HTR in one pass.

---

## P

### Pagefind
The static, client-side search library used on Ficherito sites. Indexes the built site after Eleventy runs.

### Pipeline
The sequence of processing steps: Extract → Entities → Build (with Translate as an optional, separate step). See [Pipeline Concepts](../concepts/pipeline.md).

### Prompt
Instructions given to the LLM. Ficherito uses `prompts.text_extraction` for transcription cleanup and `prompts.ner_extraction` for entity extraction, both customizable in `ficherito.yaml`.

---

## Q

### Qwen-VL
A vision-language model from Alibaba, hosted via DashScope. Ficherito's default model for transcription and entity extraction.

---

## S

### Static Site
A website made of plain HTML files (no server-side processing). Ficherito generates static sites that can be hosted anywhere.

### Sveltia CMS
A browser-based content editor mounted at `/admin/` on a deployed Ficherito site. Lets collaborators edit transcriptions, translations, and entities without touching git or Markdown directly — commits go straight to the repository via the GitHub API.

---

## T

### Transcription
The process of converting a document image to text, and the resulting Markdown file itself (`transcriptions/<id>.md`).

### Typer
The Python library Ficherito's CLI is built with.

---

## U

### undate
The Python library Ficherito uses to parse and sort partial or uncertain dates (year-only, year-month, or full day) extracted from filenames.

---

## V

### Virtual Environment (venv)
An isolated Python installation. Keeps Ficherito's dependencies separate from other projects.

### Vision-Language Model
An AI model that can process both images and text. Qwen-VL is a vision-language model.

---

## Y

### YAML
A human-readable data format. Ficherito configuration uses YAML (`ficherito.yaml`), as does the frontmatter in transcription and site content files.

---

## See Also

- **[FAQ](faq.md)** - Frequently asked questions
- **[Troubleshooting](troubleshooting.md)** - Problem solutions
- **[Concepts](../concepts/pipeline.md)** - How Ficherito works
