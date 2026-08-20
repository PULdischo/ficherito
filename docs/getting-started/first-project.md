# Your First Project

This tutorial walks you through a complete Ficherito project from start to finish, using your own historical document images.

---

## What We'll Cover

1. Preparing your document images
2. Configuring Ficherito
3. Running the pipeline step by step
4. Reviewing and editing outputs
5. Building, previewing, and deploying your site

**Time needed:** 30-45 minutes

---

## Before You Begin

Make sure you have:

- [ ] Ficherito installed ([Installation Guide](installation.md))
- [ ] An API key ready ([Getting an API Key](installation.md#step-5-get-an-api-key))
- [ ] A folder of document images

---

## Part 1: Preparing Your Documents

See [Preparing Your Images](creating-datasets.md) for naming and format
recommendations. In short: clear scans (300 DPI+), one page per image, and
filenames that include a date if you have one (`1863-04-15_page1.jpg`) —
Ficherito uses it to sort documents chronologically and to drive Browse by
Date.

---

## Part 2: Setting Up Your Project

### Create the Project

```bash
cd ~/ficherito-projects
mkdir civil-war-letters && cd civil-war-letters
ficherito init
```

### Add Your Images

```bash
cp /path/to/scans/*.jpg images/
```

### Configure Your API Key

`ficherito init` already created `.env` — edit it:

```bash
nano .env
```

```bash
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=qwen-vl-max
```

### Configure the Project

Edit `ficherito.yaml`:

```yaml
dataset:
  images_dir: "images"
  recursive: false

processing:
  extract_entities: true
  entity_context: true  # e.g. "Person; the letter's recipient"

# Custom prompt (optional — the default works well for most documents)
prompts:
  text_extraction: |
    You are a historical document transcription assistant working with
    Civil War era letters. Given the raw OCR output from a handwritten
    document, clean up and correct the text while:

    1. Preserving original 19th-century spelling conventions
    2. Maintaining original punctuation style
    3. Fixing obvious OCR errors
    4. Marking unclear portions with [?]

    Raw OCR text:
    {raw_text}

    Cleaned transcription:

website:
  title: "Civil War Family Letters"
  password: "family2026"
```

### Validate Your Configuration

```bash
ficherito validate
```

---

## Part 3: Running the Pipeline Step by Step

`ficherito process` runs everything at once, but let's go through each step individually.

### Step 1: Extract Text

```bash
ficherito extract
```

**Output:** A Markdown transcription per document in `transcriptions/`, e.g. `transcriptions/1863-04-15_page1.md`.

### Step 2: Extract Entities

```bash
ficherito entities
```

**Output:** Entities are saved to `entities/`:

```json
{
  "source_image": "1863-04-15_page1",
  "extracted_at": "2026-01-15T14:35:00Z",
  "entities": [
    {
      "text": "Sarah",
      "type": "PERSON",
      "context": "Person; the recipient of the letter, likely the writer's wife"
    },
    {
      "text": "Gettysburg",
      "type": "LOCATION",
      "context": "Location; a town in Pennsylvania mentioned as the army's destination"
    }
  ]
}
```

A `consolidated.json` file grouping all entities by type is generated too.

### Step 3: Build the Website

```bash
ficherito build
```

This emits Markdown + frontmatter + images into `site/`, then runs Eleventy
and Pagefind:

```
Installing site dependencies (npm install)...
Running Eleventy build...
✓ Site built to site/_site/
```

---

## Part 4: Reviewing and Editing

### Editing Transcriptions

Sometimes the AI makes mistakes. Edit the Markdown files directly:

```bash
nano transcriptions/1863-04-15_page1.md
```

Then rebuild:

```bash
ficherito build
```

### Editing Entities

```bash
nano entities/1863-04-15_page1.json
```

You can correct misidentified entities, add missing ones, or improve
context descriptions — then rebuild.

### Editing via the CMS Instead

Once deployed, collaborators can make both kinds of edits — transcription
text and entities — through the Sveltia CMS at `/admin/` instead of editing
files directly. See [Deployment](../usage/deployment.md#editing-content-with-sveltia-cms).

---

## Part 5: Preview and Deploy

### Preview Locally

```bash
ficherito serve
```

Open [http://localhost:8000](http://localhost:8000) to see your site.

### Deploy to the Web

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/civil-war-letters.git
git push -u origin main
```

Then add the GitHub Actions workflow and enable Pages — see
[Deployment](../usage/deployment.md#deploying-to-github-pages) for the full
steps.

---

## Summary

You've now completed a full Ficherito project:

- ✅ Prepared and organized document images
- ✅ Configured a Ficherito project
- ✅ Extracted text from historical handwriting
- ✅ Identified named entities with context
- ✅ Built and deployed a searchable, editable website

---

## Next Steps

- **[Configuration Deep Dive](../usage/configuration.md)** - Customize prompts and settings
- **[Processing Documents](../usage/processing-documents.md)** - Handle large collections
- **[Troubleshooting](../help/troubleshooting.md)** - Solve common problems
