# Summarization

Learn how Flatfish generates AI-powered summaries, timelines, and research questions from your document collections.

---

## What Summarization Produces

When you run `flatfish summarize`, you get:

| Output | Description |
|--------|-------------|
| **Finding Aid** | Professional archival description (DACS format) |
| **Timeline** | Chronological list of events |
| **Key Changes** | Significant changes across documents |
| **Research Questions** | Scholarly questions for further investigation |

---

## How It Works

Flatfish processes documents in batches, then combines the results:

```
Documents (sorted by date)
    │
    ▼
┌─────────────────────────────────────┐
│ Batch 1: Docs 1-20                  │──▶ 4 parallel tracks
│ Batch 2: Docs 21-40                 │    • Timeline events
│ Batch 3: Docs 41-60                 │    • Key changes
│ ...                                 │    • Research questions
└─────────────────────────────────────┘    • Narrative summary
    │
    ▼
┌─────────────────────────────────────┐
│ Combine results from all batches    │
│ using hierarchical merging          │
└─────────────────────────────────────┘
    │
    ▼
Final summary files
```

### Track-Based Processing

Each batch runs 4 parallel API calls:

1. **Timeline Track** - Extract dated events
2. **Key Changes Track** - Identify transformations
3. **Research Questions Track** - Generate scholarly questions
4. **Narrative Track** - Summarize content

This ensures high-quality output for each category.

---

## Running Summarization

```bash
flatfish summarize
```

**Prerequisites:** You must run `flatfish extract` first.

### For Large Collections

If you have many documents and summarization is interrupted:

```bash
# Resume from where you left off
flatfish summarize

# Or just re-run the combining step
flatfish combine
```

Batch files are saved in `summaries/batches/`, so you don't lose progress.

---

## Output Files

Summarization creates several files in `summaries/`:

### finding_aid.txt

A professional archival finding aid following DACS (Describing Archives: A Content Standard):

```markdown
## Collection Overview
- **Creator**: N.C. Marshall (1875-1945), farmer and merchant
- **Title**: Marshall Family Papers
- **Dates**: 1913-1918 (bulk 1913-1915)
- **Extent**: 6,743 documents

## Biographical/Historical Note
Norman Clarence Marshall was born in rural Pennsylvania...

## Scope and Content
This collection consists primarily of diary entries...

## Historical Significance
These documents provide rare insight into...
```

### timeline.txt

Editable chronological events:

```
# Timeline of Events
# Format: DATE | EVENT DESCRIPTION
# Edit this file to correct or add events.

1913-01-01 | Marshall begins keeping a daily diary
1913-01-15 | First mention of illness in the family
1913-02-03 | Trip to Philadelphia for business
1913-03-21 | Spring planting begins
```

### key_changes.txt

Significant changes identified across documents:

```
# Key Changes
# Format: [CATEGORY] Description
# Edit this file to correct or add changes.

[Geographic] Marshall family moves from Chester to Philadelphia in March 1914
[Economic] Transition from farming to mercantile business, 1913-1915
[Social] Marriage of eldest daughter in June 1914
[Health] Period of illness affecting family productivity, winter 1913
```

### research_questions.txt

Scholarly research questions:

```
# Research Questions
# Edit freely - add your own questions!

1. How did rural Pennsylvania families navigate the economic transition 
   from agriculture to commerce in the early 20th century?
   WHY THIS MATTERS: Complicates narratives of rapid urbanization...

2. What role did informal credit networks play in small-town commerce?
   WHY THIS MATTERS: Contributes to history of capitalism literature...
```

---

## Editing Summary Files

All summary files are designed for human editing.

### Edit the Timeline

```bash
nano summaries/timeline.txt
```

Format: `DATE | DESCRIPTION`

```
# Correct a date
1913-01-15 | First mention of illness  # Changed from 01-16

# Add a new event
1913-04-20 | Easter celebration mentioned
```

### Edit Key Changes

```bash
nano summaries/key_changes.txt
```

Format: `[CATEGORY] Description`

```
# Add a category
[Religious] Increased church attendance during revival, spring 1913

# Correct a description
[Economic] Family purchases mercantile store (not "opens business")
```

### Edit Research Questions

```bash
nano summaries/research_questions.txt
```

Add your own research questions based on your expertise:

```
# Your custom questions
15. How does this collection compare to other Pennsylvania diaries 
    of the same period?
    WHY THIS MATTERS: Could establish regional patterns...
```

### Rebuild After Editing

```bash
flatfish build
```

Your edits will appear on the website.

---

## Configuration Options

### Sample Size

For large collections, limit documents included in the summary:

```yaml
summary:
  sample_size: 100  # Use 100 documents (evenly sampled across date range)
```

### Model Selection

```yaml
summary:
  model: "qwen-vl-max"    # Best quality (default)
  # model: "qwen-vl-plus"  # Faster and cheaper
```

### Disable Sections

```yaml
website:
  show_timeline: true
  show_key_changes: true
  show_research_questions: false  # Hide this section
```

---

## Understanding the Finding Aid

The finding aid follows archival standards for describing collections:

### Collection Overview

Basic metadata about the collection:
- **Creator**: Who made these documents
- **Title**: Descriptive name
- **Dates**: Inclusive and bulk dates
- **Extent**: Number of documents

### Biographical/Historical Note

Context about the creator and time period:
- Life history
- Career and accomplishments
- Historical context
- Why documents were created/preserved

### Scope and Content

What's in the collection:
- Types of documents
- Major topics and themes
- Geographic locations
- Key people and organizations
- Notable or unusual items

### Historical Significance

Why the collection matters:
- Research value
- Historical contribution
- Perspectives represented
- Potential uses

---

## Troubleshooting

### Empty Timeline

**Problem:** Timeline has no events.

**Causes:**
- Documents don't contain dated events
- Date format not recognized

**Solution:** Check your transcriptions for date mentions. The AI needs explicit dates to build a timeline.

### Generic Research Questions

**Problem:** Questions are too broad.

**Solution:** The AI needs specific content to generate specific questions. Make sure your transcriptions are accurate and complete.

### Summarization Timeout

**Problem:** `Error: Request timed out`

**Causes:**
- Very large batches
- Complex documents
- Network issues

**Solution:**
```bash
# Just re-run - completed batches are saved
flatfish summarize

# Or combine existing batches
flatfish combine
```

### Missing Key Changes

**Problem:** Important changes not identified.

**Solution:** The AI may miss domain-specific changes. Add them manually to `key_changes.txt`.

---

## Advanced: Custom Summary Prompts

For specialized collections, customize the summary prompts:

```yaml
prompts:
  summary: |
    You are a historian specializing in 19th-century American social history.
    Analyze these documents with attention to:
    
    1. Gender and family dynamics
    2. Economic conditions and class
    3. Religious life and moral frameworks
    4. Regional identity and community
    
    ## Timeline
    Focus on events that illuminate social history...
    
    ## Key Changes
    Look for shifts in family structure, economic status...
    
    ## Research Questions
    Frame questions in terms of recent historiography...
```

---

## Next Steps

- **[Building Sites](building-sites.md)** - Create your website
- **[Deployment](deployment.md)** - Share with the world
- **[Command Reference](../commands/summarize.md)** - Full command options
