# Command Reference

Complete reference for all Ficherito CLI commands.

---

## Overview

Ficherito uses a simple command structure:

```bash
ficherito <command> [options]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `init` | Create a new project |
| `validate` | Validate configuration and API connections |
| `process` | Run the full pipeline (extract + entities + build) |
| `extract` | Extract text from images |
| `entities` | Extract named entities |
| `translate` | Translate transcriptions |
| `build` | Build the website (emits content, runs Eleventy + Pagefind) |
| `serve` | Preview site locally |
| `status` | Show processing status |
| `deploy` | Deploy to Netlify |

---

## Global Options

```bash
ficherito --help              # Show help
ficherito --version           # Show version
ficherito <cmd> --config FILE # Use a specific config file (default: ficherito.yaml)
```

---

## Quick Reference

```bash
# Start a new project
mkdir my-collection && cd my-collection
ficherito init

# Run everything
ficherito process

# Run specific steps
ficherito extract
ficherito entities
ficherito translate

# Build and preview
ficherito build
ficherito serve

# Deploy
ficherito deploy         # Netlify
# — or push to GitHub after `ficherito build`; see the deployment guide for GitHub Pages
```

---

## Command Details

- **[init](init.md)** - Initialize a new project
- **[process](process.md)** - Full pipeline execution
- **[extract](extract.md)** - Text extraction
- **[entities](entities.md)** - Named entity recognition
- **[translate](translate.md)** - Translation to target language
- **[build](build.md)** - Website generation
- **[serve](serve.md)** - Local preview server
- **[deploy](deploy.md)** - Deployment to Netlify

`validate` and `status` don't have dedicated pages — see their
`--help` output, or [Processing Documents](../usage/processing-documents.md#checking-processing-status).

---

## Common Workflows

### New Project

```bash
mkdir letters-collection && cd letters-collection
ficherito init
# Add your images to images/
ficherito process
```

### Reprocess Specific Documents

```bash
# Only redo entities (keep transcriptions)
rm entities/document_123.json
ficherito entities
```

### Development Preview

```bash
ficherito build
ficherito serve
# Open http://localhost:8000
```

---

## Environment Variables

Read from `.env` in the project directory:

```bash
OPENAI_BASE_URL      # LLM endpoint (default: provider default if unset)
OPENAI_API_KEY        # Required for extract/entities
OPENAI_MODEL           # Model name (default: provider default if unset)
NETLIFY_TOKEN          # Required for `ficherito deploy`
NETLIFY_SITE_ID        # Optional, or set website.netlify_site_id in ficherito.yaml
```

---

## Getting Help

```bash
# General help
ficherito --help

# Command-specific help
ficherito process --help
ficherito build --help
```
