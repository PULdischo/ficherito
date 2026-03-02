# flatfish entities

Extract named entities (people, places, dates, organizations) from transcribed documents.

---

## Usage

```bash
flatfish entities [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `flatfish.yaml` |
| `--source` | `-s` | Transcriptions directory | `transcriptions/` |
| `--output` | `-o` | Output directory | `entities/` |
| `--model` | `-m` | spaCy model to use | `en_core_web_lg` |
| `--force` | `-f` | Reprocess existing | `False` |
| `--file` | | Process single file | |
| `--verbose` | `-v` | Verbose output | `False` |

---

## What It Does

The `entities` command:

1. Reads transcription JSON files
2. Runs spaCy NER on the text
3. Extracts and categorizes named entities
4. Saves entity data with context

```
transcriptions/
├── letter_001.json  → entities/letter_001.json
├── letter_002.json  → entities/letter_002.json
└── ...
```

---

## Examples

### Extract All Entities

```bash
flatfish entities
```

### Process Single File

```bash
flatfish entities --file transcriptions/letter_001.json
```

### Use Different Model

```bash
flatfish entities --model en_core_web_trf
```

### Force Reprocessing

```bash
flatfish entities --force
```

---

## Output Format

```json
{
  "source_file": "letter_001.json",
  "processed_at": "2024-01-15T10:35:00",
  "model": "en_core_web_lg",
  "entities": [
    {
      "text": "John Smith",
      "label": "PERSON",
      "start": 45,
      "end": 55,
      "confidence": 0.96,
      "context": "...letter from John Smith regarding the..."
    },
    {
      "text": "Philadelphia",
      "label": "GPE",
      "start": 89,
      "end": 101,
      "confidence": 0.99,
      "context": "...traveling to Philadelphia next week..."
    },
    {
      "text": "March 15, 1865",
      "label": "DATE",
      "start": 12,
      "end": 26,
      "confidence": 0.98,
      "context": "Dated March 15, 1865\n\nDear Brother..."
    }
  ],
  "summary": {
    "PERSON": 5,
    "GPE": 3,
    "DATE": 2,
    "ORG": 1
  }
}
```

---

## Entity Types

spaCy recognizes these entity types:

| Label | Description | Examples |
|-------|-------------|----------|
| `PERSON` | People, including fictional | John Smith, Dr. Wilson |
| `GPE` | Countries, cities, states | Philadelphia, Virginia |
| `LOC` | Non-GPE locations | Mississippi River, the farm |
| `ORG` | Organizations | Congress, First Bank |
| `DATE` | Dates or periods | March 15, 1865, yesterday |
| `TIME` | Times | 3 o'clock, noon |
| `MONEY` | Monetary values | $500, fifty dollars |
| `EVENT` | Named events | the war, election |
| `FAC` | Facilities | the mill, church |
| `NORP` | Nationalities, groups | American, Baptist |

---

## Configuration

### flatfish.yaml Settings

```yaml
entities:
  # spaCy model (sm, md, lg, or trf)
  model: en_core_web_lg
  
  # Minimum confidence to keep
  min_confidence: 0.7
  
  # Entity types to extract
  types:
    - PERSON
    - GPE
    - LOC
    - DATE
    - ORG
    
  # Context window (characters around entity)
  context_window: 50
```

### Custom Entity Lists

```yaml
entities:
  # Known entities for better recognition
  custom_persons:
    - "John Smith"
    - "Mary Williams"
    - "Gen. Harrison"
    
  custom_places:
    - "Maple Grove Farm"
    - "Smith Mill"
    - "Old Lancaster Road"
```

---

## spaCy Models

### Available Models

| Model | Size | Accuracy | Speed |
|-------|------|----------|-------|
| `en_core_web_sm` | 12 MB | Good | Fast |
| `en_core_web_md` | 40 MB | Better | Medium |
| `en_core_web_lg` | 560 MB | Best | Slower |
| `en_core_web_trf` | 438 MB | Excellent | Slowest |

### Installing Models

```bash
# Install the large model (recommended)
python -m spacy download en_core_web_lg

# Or transformer model for best accuracy
python -m spacy download en_core_web_trf
```

### Non-English Models

```bash
# German
python -m spacy download de_core_news_lg

# French
python -m spacy download fr_core_news_lg

# Spanish
python -m spacy download es_core_news_lg
```

Configure in yaml:

```yaml
entities:
  model: de_core_news_lg
```

---

## Progress Output

```
Flatfish Entities
═════════════════

Processing 500 transcriptions

Document 1/500: letter_001.json
  ✓ Found 8 entities (3 PERSON, 2 GPE, 2 DATE, 1 ORG)

Document 2/500: letter_002.json
  ✓ Found 5 entities (2 PERSON, 2 DATE, 1 GPE)

...

═════════════════
Complete: 500/500 documents
Total entities: 3,456
  PERSON: 1,245
  GPE: 892
  DATE: 756
  ORG: 234
  LOC: 189
  OTHER: 140
```

---

## Aggregated Entity Report

Generate a summary across all documents:

```bash
flatfish entities --report
```

Output: `entities/entity_report.json`

```json
{
  "total_documents": 500,
  "total_entities": 3456,
  "by_type": {
    "PERSON": {
      "count": 1245,
      "unique": 89,
      "top": [
        {"text": "John Smith", "count": 156},
        {"text": "Mary Williams", "count": 98},
        {"text": "William Smith", "count": 87}
      ]
    },
    "GPE": {
      "count": 892,
      "unique": 34,
      "top": [
        {"text": "Philadelphia", "count": 234},
        {"text": "Lancaster", "count": 89}
      ]
    }
  },
  "cooccurrence": [
    {"entities": ["John Smith", "Philadelphia"], "count": 45},
    {"entities": ["John Smith", "William Smith"], "count": 38}
  ]
}
```

---

## Entity Normalization

Map variations to canonical forms:

```yaml
entities:
  normalization:
    "Jno. Smith": "John Smith"
    "J. Smith": "John Smith"
    "Mr. Smith": "John Smith"
    "Phila.": "Philadelphia"
    "N.Y.": "New York"
```

Or use a CSV file:

```yaml
entities:
  normalization_file: "entity_mappings.csv"
```

```csv
# entity_mappings.csv
original,normalized
"Jno. Smith","John Smith"
"J. Smith","John Smith"
"Phila.","Philadelphia"
```

---

## Troubleshooting

### Missing Entities

If expected entities aren't found:

1. Check transcription quality
2. Try larger spaCy model
3. Add to custom entity list
4. Adjust minimum confidence

### False Positives

If too many incorrect entities:

1. Increase minimum confidence
2. Filter by entity type
3. Use post-processing rules

### Performance Issues

For large collections:

```yaml
entities:
  # Disable less important features
  context_window: 0  # Don't extract context
  
  # Limit entity types
  types:
    - PERSON
    - GPE
    - DATE
```

---

## See Also

- **[Named Entity Recognition](../concepts/named-entities.md)** - NER concepts
- **[Entities Usage Guide](../usage/entities.md)** - Practical guide
- **[Configuration](../usage/configuration.md)** - Full configuration reference
