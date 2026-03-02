# Hierarchical Combining

How Flatfish combines hundreds of batch summaries without exceeding AI context limits.

---

## The Problem

Imagine you have a large collection:
- 500 documents
- 25 batches (20 documents each)
- 4 tracks per batch
- = 100 batch files to combine

Sending all 100 files to an AI at once would exceed context limits (typically 32K-128K tokens).

---

## The Solution: Hierarchical Combining

Instead of combining everything at once, Flatfish uses a **tree structure**:

```
Level 0: 337 batch summaries
         ├── Group 1 (batches 1-50)   ──→ Intermediate 1
         ├── Group 2 (batches 51-100) ──→ Intermediate 2
         ├── Group 3 (batches 101-150)──→ Intermediate 3
         ├── Group 4 (batches 151-200)──→ Intermediate 4
         ├── Group 5 (batches 201-250)──→ Intermediate 5
         ├── Group 6 (batches 251-300)──→ Intermediate 6
         └── Group 7 (batches 301-337)──→ Intermediate 7
                                              │
Level 1: 7 intermediate summaries ────────────┘
         └── Combined ──→ Final Summary
```

---

## How It Works

### Step 1: Group Batches

Split batch files into manageable groups:

```python
MAX_COMBINE_CHARS = 80000  # Context limit
BATCH_GROUP_SIZE = 50       # Files per group

# 337 batches → 7 groups
# [1-50], [51-100], [101-150], [151-200], [201-250], [251-300], [301-337]
```

### Step 2: Combine Each Group

Send each group to the AI:

```
Group 1 (batches 1-50):
  "Combine these 50 timeline summaries into one coherent timeline..."
  
  → Intermediate Timeline 1
```

### Step 3: Check Result Size

If intermediates still too large, recurse:

```python
if total_chars(intermediates) > MAX_COMBINE_CHARS:
    # Combine intermediates hierarchically
    return hierarchical_combine(intermediates)
else:
    # Final combination
    return combine(intermediates)
```

### Step 4: Final Combination

Combine intermediates into final output:

```
Intermediate 1 ─┐
Intermediate 2 ─┤
Intermediate 3 ─┼─→ Final Timeline
Intermediate 4 ─┤
...            ─┘
```

---

## Visual Example

For a collection with 337 batches:

```
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 0: 337 batch files                                    │
│                                                             │
│ batch_001 batch_002 ... batch_050 │ batch_051 ... batch_100 │
│ └───────────────┬────────────────┘ └───────────┬───────────┘│
│                 ▼                              ▼            │
│           Intermediate 1                 Intermediate 2     │
│                                                             │
│ batch_101 ... batch_150 │ batch_151 ... batch_200          │
│ └───────────┬───────────┘ └───────────┬───────────┘        │
│             ▼                         ▼                     │
│       Intermediate 3            Intermediate 4              │
│                                                             │
│ ... (continues for all 337 batches)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: 7 intermediate summaries                           │
│                                                             │
│ Int_1  Int_2  Int_3  Int_4  Int_5  Int_6  Int_7            │
│ └──────────────────────┬────────────────────────┘          │
│                        ▼                                    │
│                 Final Summary                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Implementation

```python
async def _hierarchical_combine(
    self,
    batch_contents: list[str],
    combine_prompt: str,
    track_name: str
) -> str:
    """Recursively combine batches in manageable groups."""
    
    # Check if all content fits in context
    total_chars = sum(len(c) for c in batch_contents)
    
    if total_chars <= MAX_COMBINE_CHARS:
        # Base case: combine directly
        combined_text = "\n\n---\n\n".join(batch_contents)
        return await self._call_api(combine_prompt, combined_text)
    
    # Recursive case: split into groups
    groups = []
    for i in range(0, len(batch_contents), BATCH_GROUP_SIZE):
        group = batch_contents[i:i + BATCH_GROUP_SIZE]
        groups.append(group)
    
    # Combine each group
    intermediates = []
    for group in groups:
        group_text = "\n\n---\n\n".join(group)
        intermediate = await self._call_api(combine_prompt, group_text)
        intermediates.append(intermediate)
    
    # Recurse on intermediates
    return await self._hierarchical_combine(
        intermediates, combine_prompt, track_name
    )
```

---

## Parameters

### MAX_COMBINE_CHARS

Maximum characters to send in one API call:

```python
MAX_COMBINE_CHARS = 80000
```

**Calculation**:
- Average: ~4 characters per token
- 80,000 chars ≈ 20,000 tokens
- Leaves room for prompt + response
- Works with 32K context window

**Adjust if needed**:
```yaml
# flatfish.yaml
summary:
  max_combine_chars: 100000  # For larger context models
```

### BATCH_GROUP_SIZE

Number of batches to combine at once:

```python
BATCH_GROUP_SIZE = 50
```

**Tradeoffs**:
- Larger: Fewer levels, more context per call
- Smaller: More levels, less context per call

---

## Track-Specific Combining

Each track has optimized combining prompts:

### Timeline Combining

```
Combine these chronological timeline sections into a single 
coherent timeline:

1. Merge overlapping events (same date/event)
2. Resolve conflicts (prefer more detailed version)
3. Maintain strict chronological order
4. Preserve date formats: YYYY-MM-DD
5. Keep cause-effect relationships clear
```

### Key Changes Combining

```
Synthesize these theme analyses into a comprehensive overview:

1. Group related themes together
2. Track how themes evolve across the timeline
3. Identify major turning points
4. Note conflicting interpretations
5. Prioritize themes by significance
```

### Research Questions Combining

```
Consolidate these research questions:

1. Remove duplicate questions
2. Merge similar questions
3. Group by topic/theme
4. Prioritize by importance
5. Remove questions answered elsewhere
```

---

## Information Preservation

### Challenge

Each level of combining risks losing details:

```
100 pages → 10 pages → 1 page
           (90% lost) (90% lost)
           = 99% total information loss!
```

### Solution: Smart Summarization

The combining prompts emphasize:

1. **Key facts** - Always preserve dates, names, numbers
2. **Unique information** - Don't lose rare details
3. **Relationships** - Maintain cause-effect links
4. **Context** - Keep enough for understanding

### Quality Checks

After combining, verify:

- ✅ Major events present
- ✅ Key names preserved
- ✅ Date range accurate
- ✅ Themes identified
- ✅ No hallucinations

---

## Performance

### API Calls Required

For 337 batches:

| Level | Groups | Calls per Track | Total Calls |
|-------|--------|-----------------|-------------|
| 0→1 | 7 | 7 | 28 |
| 1→Final | 1 | 1 | 4 |
| **Total** | | | **32** |

Without hierarchical combining: Would need to somehow fit 337 files in one call (impossible).

### Time Estimates

```
Level 0→1:  7 groups × 4 tracks = 28 calls × ~5s = ~2 minutes
Level 1→2:  1 call × 4 tracks = 4 calls × ~10s = ~40 seconds
────────────────────────────────────────────────────────────
Total combining time: ~3 minutes
```

---

## Debugging

### View Intermediate Results

Intermediates are saved for debugging:

```
batches/
├── timeline/
│   ├── batch_001.md
│   ├── ...
│   └── _intermediate_1.md  # Level 1 intermediate
│   └── _intermediate_2.md
└── ...
```

### Common Issues

**Issue**: Final summary too short

**Cause**: Over-compression at multiple levels

**Solution**: Increase `MAX_COMBINE_CHARS` or decrease `BATCH_GROUP_SIZE`

---

**Issue**: Final summary repetitive

**Cause**: Similar batches combined separately

**Solution**: Reorder batches chronologically before processing

---

**Issue**: Missing important details

**Cause**: Details lost in combining

**Solution**: Add explicit preservation instructions to combine prompt:

```yaml
prompts:
  combine_timeline: |
    MUST PRESERVE:
    - All named individuals
    - All specific dates
    - All monetary amounts
    - All place names
    
    Combine these timeline sections...
```

---

## Best Practices

### 1. Process Chronologically

Order documents by date before batching:
- Similar content grouped naturally
- Combining produces coherent narratives

### 2. Review Intermediates

Check intermediate files before final combine:
- Catch errors early
- Adjust prompts if needed

### 3. Iterative Refinement

1. Run initial combine
2. Review output
3. Adjust parameters/prompts
4. Re-run if needed

### 4. Version Control

Track changes to intermediates:

```bash
git add batches/timeline/_intermediate_*.md
git commit -m "Timeline intermediates - round 1"
```

---

## Technical Details

### Memory Usage

Hierarchical combining is memory-efficient:
- Only loads one group at a time
- Streams results to disk
- Doesn't hold all batches in memory

### Async Processing

Groups can be processed in parallel:

```python
# Process all groups in level simultaneously
intermediates = await asyncio.gather(
    *[combine_group(g) for g in groups]
)
```

### Fault Tolerance

If a group fails:
- Other groups continue
- Failed group can be retried
- Progress is saved

---

## Next Steps

- **[Track Summarization](track-summarization.md)** - Understanding tracks
- **[AI Summarization](ai-summarization.md)** - Overview of summarization
- **[Summarization Guide](../usage/summarization.md)** - Practical how-to
