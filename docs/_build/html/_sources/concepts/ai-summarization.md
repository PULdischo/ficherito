# AI Summarization

Understand how Flatfish uses AI to generate comprehensive summaries of document collections.

---

## The Challenge

Imagine you have:
- 500 pages of handwritten letters
- 200 diary entries
- 100 legal documents

How do you create a useful summary for researchers?

**Manual approach**: Months of reading and writing  
**Flatfish approach**: Automated AI summarization in hours

---

## Summarization Goals

Flatfish generates four types of outputs:

| Output | Purpose | Example Use |
|--------|---------|-------------|
| **Timeline** | Chronological narrative | Understanding sequence of events |
| **Key Changes** | Track evolving themes | Seeing how topics develop |
| **Research Questions** | Suggest investigations | Inspiring new research |
| **Narrative** | Flowing description | Collection overviews |

---

## The Track-Based Approach

Instead of asking one prompt to do everything, Flatfish uses **specialized tracks**:

```
┌─────────────────────────────────────────────────────────┐
│                    Document Batch                        │
│  (20 pages of transcribed text)                         │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Timeline │   │   Key    │   │ Research │
    │  Track   │   │ Changes  │   │Questions │
    └──────────┘   └──────────┘   └──────────┘
          │               │               │
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Date-    │   │ Theme    │   │ Open     │
    │ ordered  │   │ tracking │   │ questions│
    │ events   │   │ over time│   │ to       │
    │          │   │          │   │ explore  │
    └──────────┘   └──────────┘   └──────────┘
```

### Why Tracks?

1. **Focused prompts** - Each track has a specific job
2. **Better quality** - Specialized analysis beats general
3. **Parallel processing** - Run all tracks simultaneously
4. **User editing** - Edit one track without affecting others

---

## Track Details

### Timeline Track

**Goal**: Build a chronological narrative

**Prompt focus**:
- Extract all dates and events
- Identify sequences and causation
- Note temporal uncertainty

**Output format**:
```
1865-03-15: John Smith traveled to Philadelphia to meet with bankers.
1865-03-18: Meeting concluded; loan approved for $500.
1865-03-20: Smith returned home, began planning mill expansion.
```

### Key Changes Track

**Goal**: Track evolving themes

**Prompt focus**:
- Identify recurring topics
- Note shifts in sentiment or focus
- Track relationships over time

**Output format**:
```
TOPIC: Mill Operations
- Early letters: Optimistic planning
- Middle period: Financial concerns emerge
- Later period: Successful expansion

TOPIC: Family Health
- 1865-01: Wife's illness first mentioned
- 1865-06: Recovery documented
- 1865-12: Family health stabilized
```

### Research Questions Track

**Goal**: Suggest new investigations

**Prompt focus**:
- Identify gaps in documentation
- Note unexplained references
- Suggest contextual research

**Output format**:
```
QUESTION: Who was "Mr. B" mentioned in March letters?
- Context: Apparently a business partner
- Evidence needed: Other correspondence, business records

QUESTION: What was the "trouble at the mill" in June?
- Context: Referenced but not explained
- Evidence needed: Local newspapers, court records
```

### Narrative Track

**Goal**: Create flowing description

**Prompt focus**:
- Synthesize findings from other tracks
- Write accessible prose
- Balance detail with readability

**Output format**:
```
The Smith Family Papers document a pivotal period in the
family's history, spanning from 1865 to 1870. The collection
reveals John Smith's transformation from struggling farmer
to successful mill owner...
```

---

## The Batching Process

Documents are processed in batches:

```
┌─────────────────────────────────────────────┐
│ Collection: 500 documents                    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Batch 1: Documents 1-20                      │
│ Batch 2: Documents 21-40                     │
│ Batch 3: Documents 41-60                     │
│ ...                                          │
│ Batch 25: Documents 481-500                  │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Each batch processed by 4 tracks            │
│ = 100 API calls total                       │
│ (25 batches × 4 tracks)                     │
└─────────────────────────────────────────────┘
```

### Why Batching?

1. **API limits** - Most APIs have size limits
2. **Memory** - Process large collections without memory issues
3. **Fault tolerance** - If one batch fails, others succeed
4. **Progress tracking** - Monitor completion

---

## Hierarchical Combining

With many batches, combining is done hierarchically:

```
Level 0: 337 batch summaries
         │
         ▼ (combine groups of 50)
Level 1: 7 intermediate summaries
         │
         ▼ (combine again)
Level 2: 1 final summary
```

This prevents exceeding API context limits while preserving information.

---

## Editable Outputs

Final summaries are saved as plain text files:

```
output/
├── finding_aid.txt      # Overall collection guide
├── timeline.txt         # Chronological narrative
├── key_changes.txt      # Theme tracking
└── research_questions.txt # Investigation suggestions
```

### Why Text Files?

- **Easy editing** - Use any text editor
- **Version control** - Track changes with git
- **Accessibility** - No special software needed
- **Human-AI collaboration** - AI drafts, humans refine

---

## Quality Factors

### What Affects Summary Quality?

| Factor | Impact | Control |
|--------|--------|---------|
| Transcription quality | High | Good images, verify transcriptions |
| Document organization | Medium | Chronological ordering helps |
| Collection coherence | Medium | Related documents summarize better |
| Custom prompts | High | Tailor to your content |

### Signs of Good Summaries

✅ Accurate dates and names  
✅ Coherent narrative flow  
✅ Balanced coverage of collection  
✅ Specific, not vague  
✅ Suggests research directions  

### Signs of Problems

⚠️ Hallucinated facts  
⚠️ Missing major themes  
⚠️ Repetitive content  
⚠️ Vague generalities  
⚠️ Chronological confusion  

---

## Customizing Summarization

### Custom Prompts

Tailor the AI to your content:

```yaml
# flatfish.yaml
prompts:
  timeline: |
    Focus on:
    - Agricultural activities (planting, harvest)
    - Weather events
    - Market prices mentioned
    
    This is a farming family in the Midwest.
    
  key_changes: |
    Track these themes specifically:
    - Land ownership
    - Crop choices
    - Family labor vs hired help
```

### Adjusting Batch Size

Balance between context and API limits:

```yaml
summary:
  batch_size: 15  # Smaller batches for detailed analysis
  # batch_size: 30  # Larger batches for efficiency
```

---

## Comparison with Manual Summarization

| Aspect | Manual | AI-Assisted |
|--------|--------|-------------|
| Time | Weeks/months | Hours |
| Consistency | Variable | Uniform |
| Coverage | May miss items | Processes everything |
| Depth | Can be very deep | Good overview |
| Accuracy | High (with expertise) | Good (needs verification) |
| Cost | Labor intensive | API costs |

**Best approach**: AI generates draft, human expert reviews and refines.

---

## Technical Details

### Model Used

- **Qwen-VL-Max** via DashScope API
- Context window: ~32K tokens
- Processes text and images

### Combining Parameters

```python
MAX_COMBINE_CHARS = 80000  # Context limit
BATCH_GROUP_SIZE = 50      # Batches per combine step
```

### Output Formats

- **Batch files**: Markdown (`.md`)
- **Final summaries**: Plain text (`.txt`)
- **Metadata**: JSON

---

## Next Steps

- **[Track Summarization](track-summarization.md)** - Deep dive into tracks
- **[Hierarchical Combining](hierarchical-combining.md)** - Technical details
- **[Summarization Guide](../usage/summarization.md)** - How-to instructions
