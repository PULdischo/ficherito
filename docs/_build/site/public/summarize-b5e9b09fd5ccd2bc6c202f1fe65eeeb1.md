# flatfish summarize

Generate AI summaries of your document collection using track-based parallel processing.

---

## Usage

```bash
flatfish summarize [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `flatfish.yaml` |
| `--batch` | `-b` | Process specific batch number | all |
| `--tracks` | `-t` | Specific tracks to run | all |
| `--force` | `-f` | Reprocess existing summaries | `False` |
| `--resume` | `-r` | Continue from last position | `False` |
| `--combine` | | Also run combine after | `False` |
| `--verbose` | `-v` | Verbose output | `False` |

---

## What It Does

The `summarize` command:

1. Groups transcribed documents into batches
2. Processes each batch through 4 parallel tracks
3. Saves track outputs to separate directories

```
transcriptions/
├── doc_001.json
├── doc_002.json
└── ...
        │
        ▼ (group into batches)
        │
        ├─→ Timeline Track      → batches/timeline/batch_001.md
        ├─→ Key Changes Track   → batches/key_changes/batch_001.md
        ├─→ Research Questions  → batches/research_questions/batch_001.md
        └─→ Narrative Track     → batches/narrative/batch_001.md
```

---

## Examples

### Summarize All Documents

```bash
flatfish summarize
```

### Process Specific Batch

```bash
# Only process batch 5
flatfish summarize --batch 5
```

### Run Specific Tracks

```bash
# Only timeline track
flatfish summarize --tracks timeline

# Multiple tracks
flatfish summarize --tracks timeline,key_changes
```

### Resume Interrupted Run

```bash
flatfish summarize --resume
```

### Force Reprocessing

```bash
flatfish summarize --force
```

### Summarize and Combine

```bash
flatfish summarize --combine
```

---

## Track Outputs

### Directory Structure

```
batches/
├── timeline/
│   ├── batch_001.md
│   ├── batch_002.md
│   └── ...
├── key_changes/
│   ├── batch_001.md
│   └── ...
├── research_questions/
│   ├── batch_001.md
│   └── ...
└── narrative/
    ├── batch_001.md
    └── ...
```

### Example Output: timeline/batch_001.md

```markdown
## Timeline: Batch 001

### Events

**1865-03-15**
John Smith departed for Philadelphia on morning train.
Purpose: Meeting with First National Bank.

**1865-03-18**
Bank meeting concluded. Loan approved for $500 at 6% interest.
Mr. Davidson (bank officer) signed documents.

**1865-03-20**
Smith returned home via Reading Railroad.
Began planning mill expansion with brother William.
```

---

## Configuration

### flatfish.yaml Settings

```yaml
summary:
  # Batch size (images per batch)
  batch_size: 20
  
  # Maximum characters for combining
  max_combine_chars: 80000
  
  # Model to use
  model: qwen-vl-max
  
  # Tracks to enable
  tracks:
    - timeline
    - key_changes
    - research_questions
    - narrative

prompts:
  # Custom track prompts
  timeline: |
    Create a detailed chronological timeline...
    
  key_changes: |
    Identify and track evolving themes...
```

### Environment Variables

```bash
# Required: Qwen API key
DASHSCOPE_API_KEY=sk-your-key-here
```

---

## Progress Tracking

### Console Output

```
Flatfish Summarize
══════════════════

Processing 500 documents in 25 batches

Batch 1/25
  ├─ timeline        ✓
  ├─ key_changes     ✓
  ├─ research_q      ✓
  └─ narrative       ✓

Batch 2/25
  ├─ timeline        ✓
  ├─ key_changes     ████░░░░ 50%
  ...
```

### Progress File

```json
// .flatfish/summarize_progress.json
{
  "total_batches": 25,
  "completed_batches": 15,
  "current_batch": 16,
  "track_status": {
    "timeline": "complete",
    "key_changes": "in_progress",
    "research_questions": "pending",
    "narrative": "pending"
  }
}
```

---

## Parallel Processing

All 4 tracks run simultaneously for each batch:

```python
# Under the hood
results = await asyncio.gather(
    process_timeline(batch),
    process_key_changes(batch),
    process_research_questions(batch),
    process_narrative(batch),
)
```

### Performance

| Batches | Sequential | Parallel (4 tracks) |
|---------|------------|---------------------|
| 25 | ~50 min | ~15 min |
| 100 | ~200 min | ~55 min |

---

## Error Handling

### Retry on Failure

```yaml
summary:
  retry_count: 3
  retry_delay: 5  # seconds
```

### Partial Failures

If a track fails:
- Other tracks continue
- Failed track saved to retry queue
- Run with `--resume` to retry

### View Errors

```bash
cat .flatfish/summarize_errors.log
```

---

## Customizing Prompts

### Per-Track Prompts

```yaml
prompts:
  timeline: |
    Focus on:
    - Agricultural activities
    - Weather events
    - Market transactions
    
    Format each event as:
    YYYY-MM-DD: Description
    
  key_changes: |
    Track these themes:
    - Land ownership
    - Crop choices
    - Family labor
    
  research_questions: |
    Identify questions about:
    - Unexplained references
    - Missing context
    - Connections to broader history
```

### Domain-Specific Templates

```yaml
# For legal documents
prompts:
  timeline: |
    Extract legal proceedings chronologically:
    - Filing dates
    - Court appearances
    - Rulings and decisions
    
  key_changes: |
    Track case developments:
    - Arguments presented
    - Evidence introduced
    - Party positions
```

---

## Output Quality

### Good Summary Indicators

✅ Specific dates and names
✅ Clear chronological flow
✅ Relevant themes identified
✅ Actionable research questions
✅ Consistent formatting

### Problem Indicators

⚠️ Vague generalities
⚠️ Repeated information
⚠️ Missing important events
⚠️ Hallucinated content
⚠️ Inconsistent formatting

### Improving Quality

1. **Better transcriptions** - Verify OCR/HTR accuracy
2. **Custom prompts** - Tailor to your content
3. **Smaller batches** - More detail per batch
4. **Review and edit** - Human refinement

---

## Next Steps

After summarizing:

```bash
# Combine batch summaries into final outputs
flatfish combine

# Or combine during summarization
flatfish summarize --combine
```

---

## See Also

- **[combine](combine.md)** - Combine batch summaries
- **[Track Summarization](../concepts/track-summarization.md)** - How tracks work
- **[AI Summarization](../concepts/ai-summarization.md)** - Summarization concepts
