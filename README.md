# Flatfish <img width="100" src="logo.png" alt="Flatfish Logo">


Historical document analysis CLI - Extract, analyze, and present handwritten text from document images.

## Features

- 📜 **Handwritten Text Recognition (HTR)** - Extract text from historical document images
- 🏷️ **Named Entity Recognition** - Identify people, places, dates, and more with contextual descriptions
- 📊 **AI-Powered Summaries** - Generate timelines, track changes, and suggest research questions
- 🌐 **Static Website Builder** - Create searchable, browsable document collections

## Installation

```bash
pip install flatfish
```

## Quick Start

```bash
# Initialize a new project
flatfish init

# Edit configuration
nano flatfish.yaml
nano .env

# Validate setup
flatfish validate

# Process documents
flatfish process

# Preview the site
flatfish publish
```

## Configuration

### flatfish.yaml

```yaml
dataset:
  source: "username/dataset-name"
  splits:
    - "train"
  image_column: "image"

processing:
  extract_entities: true
  entity_context: true

summary:
  enabled: true
  model: "qwen-vl-max"

website:
  title: "Document Collection"
  password: "changeme"
```

### .env

```bash
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx
```

## Commands

| Command | Description |
|---------|-------------|
| `flatfish init` | Initialize a new project |
| `flatfish process` | Run the full pipeline |
| `flatfish extract` | Extract text from images only |
| `flatfish entities` | Extract entities only |
| `flatfish summarize` | Generate AI summary only |
| `flatfish build` | Build static site only |
| `flatfish publish` | Preview site locally |
| `flatfish validate` | Validate configuration |

## Output

```
project/
├── transcriptions/     # Extracted text files
├── entities/           # Entity JSON files
├── summaries/          # AI-generated summaries
└── _site/              # Built static website
```

## License

MIT
