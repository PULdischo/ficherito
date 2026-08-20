# ficherito init

Initialize a new Ficherito project in a directory.

---

## Usage

```bash
ficherito init [path] [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `path` | Directory to initialize the project in | `.` (current directory) |

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--force` | `-f` | Overwrite existing `ficherito.yaml` / `.env` | `False` |

---

## Examples

### Initialize the Current Directory

```bash
mkdir civil-war-letters && cd civil-war-letters
ficherito init
```

### Initialize a New Directory Directly

```bash
ficherito init civil-war-letters
cd civil-war-letters
```

### Force Overwrite

```bash
ficherito init --force
```

---

## Generated Files

```
civil-war-letters/
├── ficherito.yaml
├── .env                # copied from .env.example if it doesn't exist yet
├── .env.example
├── images/
├── transcriptions/
├── translations/
└── entities/
```

### ficherito.yaml

Written with Ficherito's built-in defaults — see
[Configuration](../usage/configuration.md) for the full reference.

### .env.example / .env

```bash
# OpenAI-compatible LLM endpoint (DashScope, OpenAI, local, etc.)
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=qwen-vl-max
```

---

## After Initialization

### 1. Add Your API Key

```bash
nano .env
```

### 2. Add Images

```bash
cp /path/to/scans/*.jpg images/
```

### 3. Validate

```bash
ficherito validate
```

### 4. Run the Pipeline

```bash
ficherito process
```

---

## See Also

- **[process](process.md)** - Run the full pipeline
- **[Configuration Guide](../usage/configuration.md)** - Detailed configuration
- **[First Project Tutorial](../getting-started/first-project.md)** - Step-by-step guide
