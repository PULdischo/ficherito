# Command Reference

Complete reference for all Flatfish CLI commands.

---

## Overview

Flatfish uses a simple command structure:

```bash
flatfish <command> [options]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `init` | Create a new project |
| `process` | Run the full pipeline |
| `transcribe` | Extract text from images |
| `entities` | Extract named entities |
| `summarize` | Generate AI summaries |
| `combine` | Combine batch summaries |
| `build` | Build the website |
| `serve` | Preview site locally |
| `deploy` | Deploy to hosting |

---

## Global Options

These options work with any command:

```bash
flatfish --help              # Show help
flatfish --version           # Show version
flatfish <cmd> --config FILE # Use specific config file
flatfish <cmd> --verbose     # Verbose output
flatfish <cmd> --quiet       # Minimal output
```

---

## Quick Reference

```bash
# Start a new project
flatfish init my-collection

# Run everything
flatfish process

# Run specific steps
flatfish transcribe
flatfish entities
flatfish summarize

# Build and preview
flatfish build
flatfish serve

# Deploy
flatfish deploy --platform netlify
```

---

## Command Details

See individual command pages:

- **[init](init.md)** - Initialize new project
- **[process](process.md)** - Full pipeline execution
- **[transcribe](transcribe.md)** - Text extraction
- **[entities](entities.md)** - Named entity recognition
- **[summarize](summarize.md)** - AI summarization
- **[combine](combine.md)** - Combine batch summaries
- **[build](build.md)** - Website generation
- **[serve](serve.md)** - Local preview server
- **[deploy](deploy.md)** - Deployment to hosting

---

## Common Workflows

### New Project

```bash
flatfish init letters-collection
cd letters-collection
# Add your images to images/
flatfish process
```

### Resume Interrupted Processing

```bash
# Continue from where you left off
flatfish process --resume
```

### Reprocess Specific Steps

```bash
# Only redo entities (keep transcriptions)
flatfish entities --force

# Only rebuild summaries
flatfish summarize --force
```

### Development Preview

```bash
flatfish build
flatfish serve
# Open http://localhost:8000
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | API error |
| 4 | File not found |
| 5 | Permission error |

---

## Environment Variables

Commands respect these environment variables:

```bash
DASHSCOPE_API_KEY    # Qwen API key
HF_TOKEN             # Hugging Face token
FLATFISH_CONFIG      # Default config file
FLATFISH_VERBOSE     # Enable verbose mode
```

---

## Getting Help

```bash
# General help
flatfish --help

# Command-specific help
flatfish process --help
flatfish summarize --help
```
