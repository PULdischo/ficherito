# Track-Based Summarization

A deep dive into Flatfish's specialized track system for generating comprehensive summaries.

---

## Overview

Track-based summarization processes documents through **four parallel specialized tracks**, each optimized for a specific type of analysis:

```
                    ┌─────────────────┐
                    │ Document Batch  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Timeline    │  │  Key Changes  │  │   Research    │
│    Track      │  │    Track      │  │   Questions   │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ timeline/     │  │ key_changes/  │  │ research_     │
│ batch_001.md  │  │ batch_001.md  │  │ questions/    │
│ batch_002.md  │  │ batch_002.md  │  │ batch_001.md  │
│ ...           │  │ ...           │  │ ...           │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Why Tracks?

### Single-Prompt Problems

A single prompt trying to do everything:

```
"Analyze this document. Extract dates, identify themes, 
track changes over time, note research questions, and 
write a narrative summary."
```

**Issues**:
- Prompt too complex
- Model may focus on one aspect
- Inconsistent outputs
- Hard to debug or improve

### Track-Based Solution

Each track has a **focused prompt**:

```
Timeline: "Create a chronological list of dated events..."
Key Changes: "Identify themes and track how they evolve..."
Research Questions: "What questions does this raise..."
```

**Benefits**:
- Clear, focused instructions
- Consistent output formats
- Parallel processing (4x throughput)
- Independent editing

---

## Track Specifications

### Timeline Track

**Purpose**: Build a chronological narrative of events

**Prompt**:
```
Analyze the following document batch and create a detailed 
chronological timeline of events. 

For each event:
- Extract the specific date if mentioned
- Describe what happened
- Note any participants
- Identify cause/effect relationships

Format as:
YYYY-MM-DD: Event description
```

**Output Example**:
```markdown
## Timeline: Batch 015

1865-03-15: John Smith departed for Philadelphia on business
1865-03-18: Met with First National Bank regarding mill loan
1865-03-20: Loan of $500 approved at 6% interest
1865-03-22: Returned home via Reading Railroad
1865-03-25: Began planning mill expansion with brother William
```

### Key Changes Track

**Purpose**: Track evolving themes and shifts

**Prompt**:
```
Analyze the following document batch and identify key 
changes in themes, relationships, or circumstances.

For each theme:
- Name the theme or topic
- Describe how it appears in this batch
- Note any shifts from previous state
- Identify trajectory (improving, worsening, stable)
```

**Output Example**:
```markdown
## Key Changes: Batch 015

### Financial Situation
- Status: IMPROVING
- Evidence: Loan approved, expansion planned
- Shift: From uncertainty to optimism

### Family Health
- Status: CONCERNING
- Evidence: Wife's illness mentioned twice
- Shift: New development, not previously noted

### Business Relationships
- Status: STABLE
- Evidence: Continued work with brother
- Shift: Bank relationship now established
```

### Research Questions Track

**Purpose**: Identify gaps and suggest investigations

**Prompt**:
```
Analyze the following document batch and identify questions 
that a researcher might want to investigate further.

For each question:
- State the question clearly
- Provide context from documents
- Suggest possible sources to consult
- Note importance (high/medium/low)
```

**Output Example**:
```markdown
## Research Questions: Batch 015

### Who was the bank officer mentioned as "Mr. Davidson"?
- Context: Approved the loan, seems to have prior relationship
- Sources: Bank records, local directories
- Importance: MEDIUM

### What was the "matter in Lancaster" that delayed return?
- Context: Mentioned but not explained
- Sources: Lancaster newspapers, court records
- Importance: LOW

### What was wife's illness?
- Context: Symptoms not described, treatment not mentioned
- Sources: Medical records if available, family history
- Importance: HIGH (affects family narrative)
```

### Narrative Track

**Purpose**: Generate flowing prose description

**Prompt**:
```
Based on the timeline, key changes, and research questions,
write a narrative paragraph summarizing this batch of 
documents.

Guidelines:
- Write in past tense
- Use specific details
- Maintain scholarly tone
- Balance detail with readability
```

**Output Example**:
```markdown
## Narrative: Batch 015

In mid-March 1865, John Smith undertook a consequential 
journey to Philadelphia that would shape his family's 
future. Meeting with representatives of the First National 
Bank, he secured a $500 loan at favorable terms, enabling 
the long-planned expansion of the family mill. His brother 
William's involvement in the planning suggests the business 
remained a family enterprise. However, the correspondence 
also reveals concerns about his wife's health, a new 
development that would recur in later documents.
```

---

## Directory Structure

Track outputs are organized in subdirectories:

```
batches/
├── timeline/
│   ├── batch_001.md
│   ├── batch_002.md
│   └── ... 
├── key_changes/
│   ├── batch_001.md
│   ├── batch_002.md
│   └── ...
├── research_questions/
│   ├── batch_001.md
│   ├── batch_002.md
│   └── ...
└── narrative/
    ├── batch_001.md
    ├── batch_002.md
    └── ...
```

---

## Parallel Processing

Tracks run simultaneously:

```python
# Simplified: How Flatfish processes a batch
async def process_batch(batch_text):
    # Run all 4 tracks in parallel
    results = await asyncio.gather(
        call_api(TIMELINE_PROMPT, batch_text),
        call_api(KEY_CHANGES_PROMPT, batch_text),
        call_api(RESEARCH_QUESTIONS_PROMPT, batch_text),
        call_api(NARRATIVE_PROMPT, batch_text),
    )
    return results
```

### Performance Impact

| Approach | API Calls | Time (est.) |
|----------|-----------|-------------|
| Sequential | 4n | 4x |
| Parallel tracks | 4n | 1x |

Where n = number of batches. Parallel processing gives 4x speedup.

---

## Combining Tracks

After all batches are processed, each track is combined separately:

```
timeline/batch_001.md  ─┐
timeline/batch_002.md  ─┼─→ timeline.txt
timeline/batch_003.md  ─┤
...                    ─┘

key_changes/batch_001.md  ─┐
key_changes/batch_002.md  ─┼─→ key_changes.txt
key_changes/batch_003.md  ─┤
...                       ─┘
```

### Combining Prompts

Each track has a specialized combining prompt:

**Timeline combining**:
```
Merge these timeline segments into a single coherent 
chronological narrative. Remove duplicates, resolve 
conflicts, maintain chronological order.
```

**Key Changes combining**:
```
Synthesize these theme analyses into a comprehensive 
overview. Track how each theme evolves across the full 
collection. Note major turning points.
```

---

## Customizing Tracks

### Custom Track Prompts

Override default prompts in configuration:

```yaml
# flatfish.yaml
prompts:
  timeline: |
    Create a timeline focusing on:
    - Agricultural activities (planting, harvest, weather)
    - Market activities (buying, selling, prices)
    - Travel and transportation
    
    This is a farming family in Ohio, 1850-1860.
    
  key_changes: |
    Track these specific themes:
    - Land ownership and expansion
    - Crop choices and yields
    - Labor (family vs. hired)
    - Equipment and technology
    - Debt and financial status
```

### Adding Custom Tracks

For specialized needs, extend the track system:

```yaml
# flatfish.yaml
custom_tracks:
  agricultural:
    prompt: |
      Extract all agricultural information:
      - Crops mentioned (type, quantity, condition)
      - Livestock (type, count, health)
      - Weather impacts
      - Market prices
    output_dir: agricultural
```

---

## Track Interaction

Tracks are processed independently but complement each other:

```
┌──────────────────────────────────────────────────────────┐
│                    FINDING AID                            │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Timeline   │→ │ Key Changes │→ │  Research   │      │
│  │  provides   │  │  provides   │  │  Questions  │      │
│  │  WHEN       │  │  WHAT/WHY   │  │  provide    │      │
│  │             │  │             │  │  NEXT STEPS │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
│                    ↓ ↓ ↓ ↓ ↓                             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Narrative Summary                    │   │
│  │        (synthesizes all tracks)                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Best Practices

### 1. Review Track Outputs Separately

Each track may need different corrections:
- Timeline: Check dates and sequences
- Key Changes: Verify themes are accurate
- Research Questions: Assess relevance

### 2. Use Tracks for Quality Control

If one track is poor, investigate:
- Is the source material unclear?
- Does the prompt need adjustment?
- Are there transcription errors?

### 3. Version Control Track Files

Track files are plain text—use git:

```bash
git add batches/
git commit -m "Initial track outputs"
# ... make edits ...
git commit -m "Corrected timeline dates in batch 15"
```

### 4. Iterative Improvement

1. Run initial summarization
2. Review track outputs
3. Adjust prompts based on issues
4. Re-run affected batches

---

## Troubleshooting

### Track outputs inconsistent?

Ensure prompts are specific about format:

```yaml
prompts:
  timeline: |
    FORMAT STRICTLY AS:
    YYYY-MM-DD: Event description
    
    If date uncertain, use:
    YYYY-MM-??: Event description
    YYYY-??-??: Event description
```

### Some tracks empty?

Check if source documents contain relevant content:
- No dates → empty timeline
- No themes → empty key changes
- Clear documents → few research questions

### Duplicate information across tracks?

This is expected—tracks overlap intentionally. The narrative track synthesizes them.

---

## Next Steps

- **[Hierarchical Combining](hierarchical-combining.md)** - How tracks are combined
- **[AI Summarization](ai-summarization.md)** - Overview of the summarization system
- **[Summarization Guide](../usage/summarization.md)** - Practical instructions
