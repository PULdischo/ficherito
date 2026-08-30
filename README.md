<picture>
  <source media="(prefers-color-scheme: dark)" srcset="logo-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="logo-light.png">
  <img width="100" src="logo-light.png" alt="Ficherito Logo">
</picture>

# Ficherito

Extract, analyze, and publish handwritten text from document images to a searchable static website.

## Features

- 📜 **Handwritten Text Recognition (HTR)** - Extract text from historical document images
- 🏷️ **Named Entity Recognition** - Identify people, places, dates, and more with contextual descriptions
- 🌐 **Translation** - Translate transcriptions into a target language
- 🔎 **Static Website Builder** - An 11ty + Pagefind site, editable via Sveltia CMS, deployable to GitHub Pages

## Installation

- Go to https://github.com/PULdischo/ficherito
- Click on the green "Use this template button" and "Create new repository" to work on your own computer, or "Open in a codespace" if you prefer to work in the cloud
- Give your project a name.
- Choose public if you'd like the static site to be published. You can start with private if you prefer and change later.
- Clone your new repository and install Ficherito from it using [uv](https://docs.astral.sh/uv/):

```bash
# Install uv if you don't already have it
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS/Linux
# Windows (PowerShell): powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

git clone https://github.com/<you>/<your-repo>.git
cd <your-repo>

uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

uv pip install -e .
```

Requires Python 3.10+ and, for `ficherito build`, Node.js 20+. See the
[installation guide](docs/getting-started/installation.md) for full details
and troubleshooting.

## Quick Start

```bash
# Initialize a new project
ficherito init

# Edit configuration
nano ficherito.yaml
nano .env

# Validate setup
ficherito validate

# Process documents
ficherito process

# Preview the site
ficherito serve
```

## Configuration

### ficherito.yaml

```yaml
dataset:
  images_dir: "images"
  recursive: false

processing:
  extract_entities: true
  entity_context: true
  max_output_tokens: 4096  # raise if transcriptions of dense/multi-page images get cut off

website:
  title: "Document Collection"
  password: "changeme"
```

`dataset.images_dir` accepts:

- **Images** — jpg/jpeg, png, tif/tiff, webp, bmp, gif, heic/heif
- **PDFs** — each page is rendered to a PNG (at 200 DPI) before processing; multi-page PDFs produce one page image per page

Set `dataset.recursive: true` to also pick up files in subfolders.

### .env

```bash
# OpenAI-compatible LLM endpoint (DashScope, OpenAI, local, etc.)
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=qwen-vl-max
```

## Commands

| Command | Description |
|---------|-------------|
| `ficherito init` | Initialize a new project |
| `ficherito process` | Run the full pipeline |
| `ficherito extract` | Extract text from images only |
| `ficherito entities` | Extract entities only |
| `ficherito translate` | Translate transcriptions |
| `ficherito build` | Emit content and build the 11ty + Pagefind site |
| `ficherito serve` | Preview site locally |
| `ficherito deploy` | Deploy to Netlify |
| `ficherito status` | Show processing status |
| `ficherito validate` | Validate configuration |

## Website

`ficherito build` emits Markdown + frontmatter + images into an [Eleventy](https://www.11ty.dev/)
site under `site/`, then runs Eleventy and [Pagefind](https://pagefind.app/) to
produce `site/_site/`. Content is editable afterward through [Sveltia CMS](https://github.com/sveltia/sveltia-cms)
at `/admin/`. See the [building sites guide](docs/usage/building-sites.md) for details.

## Deployment

### GitHub Pages (recommended)

Build locally, commit the site, and push — a GitHub Actions workflow
(`.github/workflows/deploy.yml`) rebuilds with Eleventy + Pagefind and
deploys on every push:

```bash
ficherito build
git add site/
git commit -m "Build site"
git push
```

See the [deployment guide](docs/usage/deployment.md) for the full setup
(enabling Pages, the workflow file, and configuring Sveltia CMS at `/admin/`
so collaborators can edit content without touching git).


## Output

```
project/
├── transcriptions/     # Extracted text files
├── entities/           # Entity JSON files
├── translations/       # Translated text files
└── site/               # Eleventy site (scaffolded on first build)
    ├── src/documents/  # Emitted document content
    └── _site/          # Built static website
```

## License

MIT

## Disclosure of Delegation to Generative AI

The authors declare the use of generative AI in the research and writing process. According to the GAIDeT taxonomy (2025), the following tasks were delegated to GAI tools under full human supervision:

- Code generation
- Code optimization

The GAI tool used was: Claude Sonnet.
Responsibility for the final manuscript lies entirely with the authors.
GAI tools are not listed as authors and do not bear responsibility for the final outcomes.
Declaration submitted by: Andrew Janco
