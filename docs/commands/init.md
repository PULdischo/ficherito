# flatfish init

Initialize a new Flatfish project with the standard directory structure.

---

## Usage

```bash
flatfish init <project-name> [options]
```

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `project-name` | Name for the project directory | Yes |

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--template` | `-t` | Project template to use | `default` |
| `--no-git` | | Skip git initialization | `False` |
| `--force` | `-f` | Overwrite existing directory | `False` |

---

## Examples

### Basic Initialization

```bash
flatfish init civil-war-letters
```

Creates:
```
civil-war-letters/
├── flatfish.yaml
├── .env.example
├── images/
│   └── .gitkeep
├── transcriptions/
├── entities/
├── summaries/
├── site/
└── README.md
```

### Initialize in Current Directory

```bash
mkdir my-project && cd my-project
flatfish init .
```

### With Specific Template

```bash
flatfish init family-papers --template diary
```

### Force Overwrite

```bash
flatfish init existing-project --force
```

---

## Generated Files

### flatfish.yaml

Default configuration file:

```yaml
# Flatfish Configuration

project:
  name: civil-war-letters
  description: ""

source:
  huggingface_repo: ""
  
processing:
  batch_size: 20
  
output:
  format: markdown
```

### .env.example

Template for environment variables:

```bash
# Rename to .env and fill in your keys

# Qwen API key (required)
DASHSCOPE_API_KEY=your-key-here

# Hugging Face token (for private repos)
HF_TOKEN=your-token-here
```

### README.md

Project documentation template:

```markdown
# civil-war-letters

A historical document collection processed with Flatfish.

## Quick Start

1. Add your document images to `images/`
2. Configure `flatfish.yaml`
3. Set up `.env` with your API keys
4. Run `flatfish process`
```

---

## After Initialization

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Add Your API Keys

Edit `.env`:
```bash
DASHSCOPE_API_KEY=sk-your-actual-key
HF_TOKEN=hf_your-actual-token
```

### 3. Configure Your Project

Edit `flatfish.yaml`:
```yaml
project:
  name: civil-war-letters
  description: "Letters from the Smith family, 1861-1865"

source:
  huggingface_repo: "username/civil-war-letters"
```

### 4. Add Images

Copy or link your document images:
```bash
cp /path/to/scans/*.jpg images/
# or
ln -s /path/to/scans images/original
```

### 5. Run Pipeline

```bash
flatfish process
```

---

## Templates

### default

Standard project structure for general use.

### diary

Optimized for diary/journal collections:
- Sequential date organization
- Personal narrative prompts
- Single-author configuration

### correspondence

Optimized for letter collections:
- Sender/recipient tracking
- Date and place emphasis
- Multiple correspondents

### legal

Optimized for legal documents:
- Formal language settings
- Party identification
- Document type classification

---

## See Also

- **[process](process.md)** - Run the full pipeline
- **[Configuration Guide](../usage/configuration.md)** - Detailed configuration
- **[First Project Tutorial](../getting-started/first-project.md)** - Step-by-step guide
