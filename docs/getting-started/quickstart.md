# Quick Start

Get up and running with Ficherito in 10 minutes! This guide assumes you've already [installed Ficherito](installation.md).

---

## Overview

In this quick start, you'll:

1. Create a new Ficherito project
2. Add a few document images
3. Run the processing pipeline
4. Preview your generated website

---

## Step 1: Create a New Project

```bash
mkdir my-first-collection && cd my-first-collection
ficherito init
```

This creates:

```
my-first-collection/
├── ficherito.yaml     # Your project configuration
├── .env                # API key (created from .env.example)
├── .env.example        # Template for API keys
├── images/             # Put your document images here
├── transcriptions/
├── translations/
└── entities/
```

---

## Step 2: Add Your API Key

`ficherito init` already created `.env` for you — just edit it:

```bash
nano .env
```

```bash
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=qwen-vl-max
```

---

## Step 3: Add Some Images

Copy a handful of document images (JPEG, PNG, TIFF, WebP, HEIC, or PDF) into `images/`:

```bash
cp /path/to/scans/*.jpg images/
```

`ficherito.yaml` already points `dataset.images_dir` at `images/`, so there's nothing else to configure for a quick test.

---

## Step 4: Validate Your Setup

```bash
ficherito validate
```

```
✓ Config file valid
✓ LLM base URL: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
✓ API key found
✓ Model: qwen-vl-max
✓ Images folder: images

Ready to process!
```

---

## Step 5: Process Your Documents

```bash
ficherito process --limit 5
```

```{tip}
`--limit 5` processes just the first 5 images — useful for a quick test before running the whole collection. Drop it to process everything.
```

This extracts text, identifies entities, and builds the website in one go:

```
Extracting text (5/5)...
Extracting entities (5/5)...
Building website...

✓ Pipeline complete!
  Transcriptions: transcriptions/
  Entities: entities/
  Website: site/_site/
```

---

## Step 6: Preview Your Site

```bash
ficherito serve
```

```
Serving at http://localhost:8000
Press Ctrl+C to stop.
```

Open [http://localhost:8000](http://localhost:8000) — you'll land on a password gate (default password: `changeme`, set via `website.password` in `ficherito.yaml`), then the search page.

---

## What You've Built

- **📄 Document pages** - Zoomable image viewer + transcription + entities, with previous/next navigation
- **🔍 Full-text search** - Powered by Pagefind
- **🏷️ Browse by Entity** - People, places, dates, and more, with mention counts
- **📅 Browse by Date** - Filterable by date range

---

## Next Steps

- **[Your First Project](first-project.md)** - A deeper dive with your own documents
- **[Configuration Guide](../usage/configuration.md)** - Customize Ficherito for your needs
- **[Deployment](../usage/deployment.md)** - Share your site with the world (GitHub Pages)

---

## Cleaning Up

```bash
# Remove all generated files
rm -rf transcriptions/ translations/ entities/ site/_site/

# Or reset the site build entirely (including the Eleventy scaffold)
rm -rf site/
```
