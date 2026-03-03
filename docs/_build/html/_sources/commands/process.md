# flatfish process

Run the complete Flatfish pipeline on your document collection.

---

## Usage

```bash
flatfish process [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `flatfish.yaml` |
| `--steps` | `-s` | Specific steps to run | all |
| `--resume` | `-r` | Continue from last position | `False` |
| `--force` | `-f` | Reprocess all files | `False` |
| `--dry-run` | | Show what would be done | `False` |
| `--verbose` | `-v` | Verbose output | `False` |
| `--quiet` | `-q` | Minimal output | `False` |

---

## Pipeline Steps

The `process` command runs these steps in order:

```
1. FETCH      → Download images from Hugging Face
2. TRANSCRIBE → Extract text using Qwen-VL
3. ENTITIES   → Identify named entities with spaCy
4. SUMMARIZE  → Generate AI summaries (4 tracks)
5. COMBINE    → Combine batch summaries
6. BUILD      → Generate website
```

---

## Examples

### Run Full Pipeline

```bash
flatfish process
```

### Run Specific Steps

```bash
# Only transcribe
flatfish process --steps transcribe

# Transcribe and extract entities
flatfish process --steps transcribe,entities

# Only build website (skip AI processing)
flatfish process --steps build
```

### Resume Interrupted Run

```bash
# If process was interrupted at batch 15
flatfish process --resume
# Continues from batch 16
```

### Force Reprocessing

```bash
# Redo everything, ignore cached results
flatfish process --force
```

### Dry Run

```bash
# See what would happen
flatfish process --dry-run

# Output:
# Would process 500 images
# Would create 25 batches
# Would generate 4 track summaries
# Would build 500 pages
```

---

## Progress Tracking

### Console Output

```
Flatfish Pipeline
═════════════════

[1/6] Fetching images...
      ✓ 500 images downloaded

[2/6] Transcribing...
      Batch 1/25 ████████████████████ 100%
      Batch 2/25 ████████████████████ 100%
      ...
      ✓ 500 documents transcribed

[3/6] Extracting entities...
      ✓ 1,247 entities found

[4/6] Generating summaries...
      Track: timeline       ████████████████████ 100%
      Track: key_changes    ████████████████████ 100%
      Track: research_q     ████████████████████ 100%
      Track: narrative      ████████████████████ 100%
      ✓ 25 batches processed

[5/6] Combining summaries...
      ✓ 4 track summaries generated

[6/6] Building website...
      ✓ 520 pages generated

═════════════════
Pipeline complete!
```

### Progress File

Progress is saved for resume capability:

```json
// .flatfish/progress.json
{
  "last_run": "2024-01-15T10:30:00",
  "step": "summarize",
  "batch": 15,
  "status": "interrupted"
}
```

---

## Configuration

Control pipeline behavior in `flatfish.yaml`:

```yaml
processing:
  # Number of images per batch
  batch_size: 20
  
  # Maximum parallel API calls
  max_concurrent: 4
  
  # Retry failed requests
  retry_count: 3
  retry_delay: 5  # seconds
  
  # Skip steps
  skip:
    - entities  # Skip NER if not needed
```

---

## Output Files

After running `process`, your directory contains:

```
project/
├── transcriptions/
│   ├── image_001.json
│   ├── image_002.json
│   └── ...
├── entities/
│   ├── image_001.json
│   └── ...
├── batches/
│   ├── timeline/
│   │   ├── batch_001.md
│   │   └── ...
│   ├── key_changes/
│   │   └── ...
│   ├── research_questions/
│   │   └── ...
│   └── narrative/
│       └── ...
├── output/
│   ├── finding_aid.txt
│   ├── timeline.txt
│   ├── key_changes.txt
│   └── research_questions.txt
└── site/
    ├── index.html
    ├── documents/
    └── ...
```

---

## Error Handling

### API Errors

```
Error: API rate limit exceeded
Retry in 60 seconds...
Attempt 2/3...
✓ Recovered
```

### Batch Failures

```
Error: Batch 15 failed
Saving progress...
Run 'flatfish process --resume' to continue
```

### Recovery Commands

```bash
# Resume from failure point
flatfish process --resume

# Retry specific batch
flatfish summarize --batch 15

# Skip problematic files
flatfish process --skip "image_corrupt.jpg"
```

---

## Performance Tips

### Optimize Batch Size

```yaml
# For large images (high detail)
processing:
  batch_size: 10

# For small images (less detail)
processing:
  batch_size: 30
```

### Parallel Processing

```yaml
# For faster API
processing:
  max_concurrent: 8

# For rate-limited API
processing:
  max_concurrent: 2
```

### Skip Unnecessary Steps

```yaml
processing:
  skip:
    - entities  # If you don't need NER
```

---

## Logging

### Enable Detailed Logs

```bash
flatfish process --verbose
```

### Log to File

```bash
flatfish process 2>&1 | tee process.log
```

### View Logs

```bash
# Recent activity
tail -f .flatfish/flatfish.log
```

---

## See Also

- **[transcribe](transcribe.md)** - Text extraction details
- **[summarize](summarize.md)** - Summarization details
- **[combine](combine.md)** - Combining batch summaries
- **[Configuration Guide](../usage/configuration.md)** - Full configuration reference
