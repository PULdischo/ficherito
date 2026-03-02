# flatfish combine

Combine batch summaries into final track outputs using hierarchical merging.

---

## Usage

```bash
flatfish combine [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `flatfish.yaml` |
| `--tracks` | `-t` | Specific tracks to combine | all |
| `--force` | `-f` | Reprocess existing outputs | `False` |
| `--verbose` | `-v` | Verbose output | `False` |

---

## What It Does

The `combine` command:

1. Reads all batch files from each track directory
2. Uses hierarchical combining to merge them
3. Outputs final summary files

```
batches/
├── timeline/
│   ├── batch_001.md      ─┐
│   ├── batch_002.md       │
│   └── ...               ─┼─→ output/timeline.txt
│
├── key_changes/
│   ├── batch_001.md      ─┐
│   └── ...               ─┼─→ output/key_changes.txt
│
├── research_questions/
│   ├── batch_001.md      ─┐
│   └── ...               ─┼─→ output/research_questions.txt
│
└── narrative/
    ├── batch_001.md      ─┐
    └── ...               ─┴─→ output/finding_aid.txt
```

---

## Examples

### Combine All Tracks

```bash
flatfish combine
```

### Combine Specific Track

```bash
# Only combine timeline
flatfish combine --tracks timeline

# Multiple tracks
flatfish combine --tracks timeline,key_changes
```

### Force Recombining

```bash
flatfish combine --force
```

---

## Output Files

Final outputs are plain text files for easy editing:

```
output/
├── finding_aid.txt        # Main collection narrative
├── timeline.txt           # Chronological events
├── key_changes.txt        # Theme evolution
└── research_questions.txt # Suggested investigations
```

### Example: timeline.txt

```
TIMELINE: Smith Family Papers (1865-1870)
==========================================

1865
----

MARCH

1865-03-15: John Smith traveled to Philadelphia for bank meeting.

1865-03-18: Loan approved by First National Bank ($500 at 6%).

1865-03-20: Smith returned home. Began mill expansion planning.

1865-03-25: William Smith joined planning efforts.

APRIL

1865-04-01: Construction materials ordered from Lancaster.

...
```

---

## Hierarchical Combining

For large collections, combining happens in levels:

```
Level 0: 337 batch files
         │
         ├── Group 1 (batches 1-50)   → Intermediate 1
         ├── Group 2 (batches 51-100) → Intermediate 2
         └── ... (7 groups total)
                                           │
Level 1: 7 intermediate summaries ─────────┘
         └── Combined → Final Output
```

### Why Hierarchical?

- API context limits (~32K tokens)
- 337 batches won't fit in one call
- Hierarchical merging preserves information

---

## Configuration

### flatfish.yaml Settings

```yaml
summary:
  # Maximum characters per combine call
  max_combine_chars: 80000
  
  # Batches per group
  batch_group_size: 50

prompts:
  # Custom combine prompts per track
  combine_timeline: |
    Merge these timeline segments:
    1. Maintain chronological order
    2. Remove duplicate events
    3. Preserve all dates and names
    
  combine_key_changes: |
    Synthesize these theme analyses:
    1. Group related themes
    2. Track evolution across time
    3. Note major turning points
```

---

## Progress Output

```
Flatfish Combine
════════════════

Combining 4 tracks from 337 batches

Track: timeline
  Level 0 → 1: Combining 7 groups...
    Group 1/7 ✓
    Group 2/7 ✓
    ...
  Level 1 → Final: Combining 7 intermediates...
  ✓ output/timeline.txt (15,234 chars)

Track: key_changes
  Level 0 → 1: Combining 7 groups...
  ...
  ✓ output/key_changes.txt (12,456 chars)

Track: research_questions
  ...
  ✓ output/research_questions.txt (8,901 chars)

Track: narrative
  ...
  ✓ output/finding_aid.txt (18,234 chars)

════════════════
Combine complete!
```

---

## Editing Outputs

Output files are plain text—edit freely:

```bash
# Open in your editor
code output/timeline.txt

# Make corrections
# - Fix dates
# - Add context
# - Correct names
```

### Version Control

Track your edits:

```bash
git add output/
git commit -m "Initial AI-generated summaries"

# After editing
git commit -m "Manual corrections to timeline"
```

---

## Detecting Track Structure

The `combine` command automatically detects directory structure:

### Track-Based (New)

```
batches/
├── timeline/
├── key_changes/
├── research_questions/
└── narrative/
```

### Legacy (Old)

```
batches/
├── batch_001.md
├── batch_002.md
└── ...
```

Both structures are supported.

---

## Troubleshooting

### "No batch files found"

Check that summarize completed:

```bash
ls batches/timeline/
# Should show batch_*.md files
```

Run summarize first:

```bash
flatfish summarize
flatfish combine
```

### "Context length exceeded"

Reduce batch group size:

```yaml
summary:
  max_combine_chars: 60000
  batch_group_size: 30
```

### Output too short

Information may be over-compressed. Try:

1. Larger `max_combine_chars`
2. More specific combine prompts
3. Review intermediate files

---

## Intermediate Files

Debug hierarchical combining:

```
batches/timeline/
├── batch_001.md
├── ...
├── _intermediate_1.md    # Level 1 intermediate
├── _intermediate_2.md
└── ...
```

Review intermediates to understand combining:

```bash
cat batches/timeline/_intermediate_1.md
```

---

## See Also

- **[summarize](summarize.md)** - Generate batch summaries
- **[Hierarchical Combining](../concepts/hierarchical-combining.md)** - How combining works
- **[Track Summarization](../concepts/track-summarization.md)** - Track system details
