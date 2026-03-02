# Named Entity Recognition

Learn how Flatfish identifies people, places, dates, and other important entities in your documents.

---

## What is NER?

**Named Entity Recognition (NER)** is the process of identifying and categorizing key information in text:

```
"John Smith traveled to Philadelphia on March 15, 1865."
 └── PERSON ──┘          └── PLACE ──┘  └── DATE ──────┘
```

NER transforms unstructured text into structured data that can be:
- Searched
- Filtered
- Analyzed
- Visualized

---

## Entity Types

Flatfish identifies these entity types:

| Type | Code | Examples |
|------|------|----------|
| Person | `PER` | John Smith, Mrs. Wilson, General Grant |
| Location | `LOC` | Philadelphia, Mississippi River, home |
| Organization | `ORG` | Congress, First National Bank |
| Date | `DATE` | March 15, 1865, yesterday, next week |
| Time | `TIME` | 3 o'clock, noon, evening |
| Money | `MONEY` | $5.00, fifty dollars, 3 shillings |
| Event | `EVENT` | the war, harvest, election |

---

## How It Works

### Step 1: Text Segmentation

Break document into sentences:

```
"I saw Mr. Jones today. He mentioned traveling to New York."
         ↓
["I saw Mr. Jones today.", "He mentioned traveling to New York."]
```

### Step 2: Entity Detection

Find entity spans:

```
"I saw Mr. Jones today."
        └─────┘
       PERSON at positions 6-15
```

### Step 3: Entity Classification

Categorize each entity:

```json
{
  "text": "Mr. Jones",
  "label": "PER",
  "start": 6,
  "end": 15,
  "confidence": 0.94
}
```

### Step 4: Coreference Resolution

Link mentions to the same entity:

```
"I saw Mr. Jones today. He was well."
        └─────┘         └─┘
        Same person!
```

---

## The NER Process in Flatfish

```
┌─────────────────┐
│ Transcribed     │
│ Document Text   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ spaCy NER       │  Identify entities using
│ Model           │  trained language model
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Entity          │  Filter by confidence
│ Filtering       │  Remove false positives
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Entity          │  Find variations and
│ Normalization   │  standard forms
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Entity          │
│ Database        │
└─────────────────┘
```

---

## Entity Output Format

Entities are stored in JSON:

```json
{
  "document": "letter_1865_03_15.jpg",
  "entities": [
    {
      "text": "John Smith",
      "label": "PER",
      "normalized": "Smith, John",
      "start": 45,
      "end": 55,
      "confidence": 0.96,
      "context": "...letter from John Smith regarding..."
    },
    {
      "text": "Philadelphia",
      "label": "LOC",
      "normalized": "Philadelphia, PA",
      "start": 89,
      "end": 101,
      "confidence": 0.99,
      "context": "...traveling to Philadelphia next week..."
    }
  ]
}
```

---

## Challenges with Historical Text

### Spelling Variations

The same name may appear different ways:

```
"Jno. Smith"     → John Smith
"J. Smith Esq."  → John Smith
"Mr Smith"       → John Smith
"John Smyth"     → John Smith (or different person?)
```

### Abbreviations

Historical documents use many abbreviations:

| Abbreviation | Meaning |
|--------------|---------|
| Jno. | John |
| Wm. | William |
| Thos. | Thomas |
| Esq. | Esquire |
| Mrs. | Mistress/Missus |
| Col. | Colonel |
| Rev. | Reverend |

### Context Dependency

Same word, different entity types:

```
"Washington" → George Washington (PERSON)
"Washington" → Washington, D.C. (LOCATION)
"Washington" → Washington Army (ORGANIZATION)
```

---

## Improving Entity Extraction

### Custom Entity Lists

Provide known entities:

```yaml
# flatfish.yaml
entities:
  custom_persons:
    - "John Smith"
    - "Mary Williams"
    - "General Harrison"
  custom_locations:
    - "Maple Grove"
    - "Smith Farm"
    - "Old Mill Road"
```

### Gazetteer Files

Reference lists for normalization:

```csv
# places.csv
original,normalized,type
"Phila.","Philadelphia, PA",city
"N.Y.","New York, NY",city
"Va.","Virginia",state
```

### Post-Processing

Manual review and correction:

1. Export entities to spreadsheet
2. Review and correct
3. Re-import corrections

---

## Entity Linking

Connect entities to external databases:

### Example: Wikidata Linking

```json
{
  "text": "Abraham Lincoln",
  "label": "PER",
  "wikidata_id": "Q91",
  "wikipedia_url": "https://en.wikipedia.org/wiki/Abraham_Lincoln"
}
```

### Example: GeoNames Linking

```json
{
  "text": "Philadelphia",
  "label": "LOC",
  "geonames_id": "4560349",
  "coordinates": {"lat": 39.9526, "lon": -75.1652}
}
```

---

## Using Entity Data

### Search Index

Find all documents mentioning a person:

```python
results = search.query(entity="John Smith", type="PER")
```

### Network Analysis

Who appears together in documents?

```
John Smith ←→ Mary Williams (5 documents)
John Smith ←→ Philadelphia (12 documents)
John Smith ←→ First Bank (3 documents)
```

### Timeline Generation

When do entities appear?

```
1865-01-15: John Smith mentioned (letter)
1865-02-20: John Smith mentioned (diary)
1865-03-15: John Smith mentioned (will)
```

### Geographic Mapping

Where do events occur?

```
Philadelphia: 12 mentions
New York: 5 mentions
Boston: 3 mentions
```

---

## Entity Statistics

Review your entity extraction:

```bash
# Count entities by type
flatfish stats entities

# Output:
# PERSON:   245 entities
# LOCATION: 189 entities
# DATE:     156 entities
# ORG:      34 entities
```

---

## spaCy Models

Flatfish uses spaCy for NER. Available models:

| Model | Size | Accuracy | Speed |
|-------|------|----------|-------|
| `en_core_web_sm` | 12 MB | Good | Fast |
| `en_core_web_md` | 40 MB | Better | Medium |
| `en_core_web_lg` | 560 MB | Best | Slower |
| `en_core_web_trf` | 438 MB | Excellent | Slowest |

Specify in configuration:

```yaml
# flatfish.yaml
nlp:
  model: en_core_web_lg
```

---

## Custom Models

For specialized documents, train custom models:

### When to Train Custom

- Domain-specific entity types
- Unusual abbreviations
- Historical spelling variations
- Non-English languages

### Training Data Format

```json
[
  ["John Smith traveled to Philadelphia.", 
   {"entities": [[0, 10, "PER"], [24, 36, "LOC"]]}],
  ["The letter is dated March 1865.", 
   {"entities": [[22, 32, "DATE"]]}]
]
```

---

## Best Practices

### 1. Start with Automatic Extraction

Let Flatfish extract entities first, then refine.

### 2. Review High-Value Documents

Focus manual review on:
- Low confidence scores
- Important documents
- Documents with many entities

### 3. Build Entity Authority Files

Maintain canonical lists of:
- People in your collection
- Places mentioned
- Organizations referenced

### 4. Document Entity Decisions

Record why you normalized entities:
- "Jno. Smith" = "John Smith" (standard abbreviation)
- Keep "Smyth" vs "Smith" separate (different families)

---

## Next Steps

- **[AI Summarization](ai-summarization.md)** - Generate collection summaries
- **[Track Summarization](track-summarization.md)** - Understand track-based approach
- **[Entities Usage Guide](../usage/entities.md)** - Practical how-to
