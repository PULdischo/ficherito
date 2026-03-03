# Entity Extraction

Learn how Flatfish identifies people, places, dates, and other named entities in your documents.

---

## What Are Named Entities?

Named entities are specific things mentioned in text that can be classified into categories:

| Type | Examples |
|------|----------|
| **PERSON** | John Smith, Mrs. Johnson, Dr. Williams |
| **LOCATION** | Philadelphia, the Delaware River, home |
| **DATE** | April 15th 1863, last Tuesday, Christmas |
| **ORGANIZATION** | the Union Army, First Presbyterian Church |
| **MONEY** | $50, five dollars, 2 shillings |
| **OCCUPATION** | blacksmith, farmer, attorney |
| **EVENT** | the battle, the election, the wedding |
| **DOCUMENT** | the deed, his will, this letter |
| **LEGAL_TERM** | plaintiff, defendant, executor |
| **RELATIONSHIP** | my brother, her husband, the children |

---

## How Entity Extraction Works

Flatfish analyzes each transcription with AI to:

1. Find all mentions of named entities
2. Classify them by type
3. Add **contextual descriptions** explaining their role

### Example Output

Input text:
> "Dear Sarah, I write to you from camp near Gettysburg. Your brother John arrived yesterday with news from home."

Extracted entities:
```json
[
  {
    "text": "Sarah",
    "type": "PERSON",
    "context": "Person; the recipient of the letter, likely the writer's wife or sweetheart"
  },
  {
    "text": "Gettysburg",
    "type": "LOCATION",
    "context": "Location; a town in Pennsylvania where the army is camped"
  },
  {
    "text": "John",
    "type": "PERSON",
    "context": "Person; Sarah's brother who brought news from home"
  },
  {
    "text": "yesterday",
    "type": "DATE",
    "context": "Date; relative date referring to the day before this letter was written"
  }
]
```

---

## Running Entity Extraction

Extract entities from all transcribed documents:

```bash
flatfish entities
```

**Prerequisites:** You must run `flatfish extract` first.

**Output:** JSON files in `entities/` directory.

---

## Understanding Contextual Descriptions

The key feature of Flatfish's entity extraction is **contextual descriptions**. Instead of just labeling "John" as a person, it explains *who John is in this document*.

### Why Context Matters

Consider "John" appearing in 50 documents:
- Document 1: "John" = the writer's son
- Document 15: "John" = a business partner
- Document 32: "John" = a different person entirely

Contextual descriptions help you understand these relationships.

### Controlling Context

Enable or disable context in your configuration:

```yaml
processing:
  entity_context: true  # Include descriptions (default)
  # entity_context: false  # Just types, no descriptions
```

---

## Customizing Entity Extraction

### Custom Entity Types

Add domain-specific entity types:

```yaml
prompts:
  ner_extraction: |
    Extract named entities from this historical legal document.
    
    Use these entity types:
    - PERSON: Individual people
    - LOCATION: Places (cities, states, properties)
    - DATE: Dates and time references
    - ORGANIZATION: Companies, churches, government bodies
    - MONEY: Monetary amounts
    - PROPERTY: Land descriptions, buildings, goods
    - LEGAL_ACTION: Lawsuits, contracts, agreements
    - WITNESS: People who witnessed or signed
    
    For each entity, explain its role in the document.
    
    Document text:
    {document_text}
```

### Specialized Collections

For specific document types:

**Military Records:**
```yaml
prompts:
  ner_extraction: |
    Extract entities from this Civil War military document.
    
    Entity types:
    - PERSON: Soldiers, officers, civilians
    - MILITARY_UNIT: Regiments, companies, divisions
    - LOCATION: Camps, battlefields, towns
    - DATE: Dates of events
    - RANK: Military ranks
    - CASUALTY: References to killed, wounded, missing
    
    Document text:
    {document_text}
```

**Genealogical Records:**
```yaml
prompts:
  ner_extraction: |
    Extract entities from this genealogical record.
    
    Entity types:
    - PERSON: All named individuals
    - RELATIONSHIP: Family relationships
    - DATE: Birth, death, marriage dates
    - LOCATION: Places of residence, birth, death
    - OCCUPATION: Jobs and professions
    - RELIGION: Churches, religious affiliations
    
    Document text:
    {document_text}
```

---

## Entity Output Format

Each document's entities are saved as JSON:

```json
{
  "document_id": "1863-04-15_page_001",
  "entities": [
    {
      "text": "Sarah",
      "type": "PERSON",
      "context": "Person; the recipient of the letter",
      "positions": [
        {"start": 5, "end": 10}
      ]
    },
    {
      "text": "Gettysburg",
      "type": "LOCATION",
      "context": "Location; a town in Pennsylvania"
    }
  ],
  "extracted_at": "2024-01-15T14:35:00Z",
  "model": "qwen-vl-max"
}
```

---

## Reviewing and Editing Entities

### View Entities for a Document

```bash
cat entities/document_001.json | jq '.entities'
```

### Edit Entities

```bash
nano entities/document_001.json
```

You can:
- Correct misidentified entities
- Add missing entities
- Improve context descriptions
- Change entity types

### Find Specific Entity Types

```bash
# Find all PERSON entities across all documents
grep -h '"type": "PERSON"' entities/*.json | sort | uniq -c | sort -rn
```

---

## Entity Statistics

After extraction, view statistics:

```bash
flatfish status --entities
```

```
Entity Statistics
═════════════════

Documents processed: 500
Total entities: 4,523

By type:
  PERSON:       1,234 (27.3%)
  LOCATION:       856 (18.9%)
  DATE:           743 (16.4%)
  ORGANIZATION:   412 (9.1%)
  MONEY:          298 (6.6%)
  OTHER:          980 (21.7%)

Unique entities: 892
Most frequent:
  Sarah (PERSON): 145 mentions
  Philadelphia (LOCATION): 89 mentions
  John (PERSON): 76 mentions
```

---

## The Entity Index

When you build your website, Flatfish creates an entity index that lets users:

- Browse all entities by type
- Click an entity to see all documents mentioning it
- See context descriptions for each mention

---

## Advanced: Entity Linking

For research projects, you might want to link entities to external databases:

### Manual Linking

Add links to your entity files:

```json
{
  "text": "Abraham Lincoln",
  "type": "PERSON",
  "context": "Person; the President mentioned in the letter",
  "links": {
    "wikipedia": "https://en.wikipedia.org/wiki/Abraham_Lincoln",
    "viaf": "https://viaf.org/viaf/76349832",
    "loc": "https://id.loc.gov/authorities/names/n79006779"
  }
}
```

### Future Feature

Automatic entity linking to Wikidata and other knowledge bases is planned for a future release.

---

## Troubleshooting

### Entities Not Extracted

**Problem:** Some documents have no entities.

**Causes:**
- Very short documents
- Documents with mostly illegible text
- Non-standard document types

**Solution:** Check the transcription quality first.

### Wrong Entity Types

**Problem:** "Philadelphia" marked as PERSON.

**Solution:** The AI sometimes makes mistakes. Edit the entity file manually or refine your prompt.

### Missing Important Entities

**Problem:** Key names not extracted.

**Solution:** Make your prompt more specific about what to look for:

```yaml
prompts:
  ner_extraction: |
    Pay special attention to:
    - All people mentioned, even by nickname or title
    - Place names, including informal references
    - Any dates, even relative ones like "last week"
    ...
```

---

## Next Steps

- **[Summarization](summarization.md)** - Generate AI summaries
- **[Building Sites](building-sites.md)** - Create your website
- **[Command Reference](../commands/entities.md)** - Full command options
