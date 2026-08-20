# Entity Extraction

Learn how Ficherito identifies people, places, dates, and other named entities in your documents.

---

## What Are Named Entities?

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

Ficherito sends each transcription to the same LLM used for HTR (an
OpenAI-compatible endpoint, configured via `.env`) with the `ner_extraction`
prompt from `ficherito.yaml`, asking it to:

1. Find all mentions of named entities
2. Classify them by type
3. Add a **contextual description** explaining each entity's role in *this*
   document (only if `processing.entity_context: true`)

### Example

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
  }
]
```

---

## Running Entity Extraction

```bash
ficherito entities
```

**Prerequisites:** Run `ficherito extract` first (entities are extracted
from transcriptions, not images directly).

**Options:**

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--limit` | `-l` | Limit number of documents | all |
| `--concurrency` | `-j` | Concurrent API requests | `10` |

Already-extracted documents are skipped on subsequent runs, so it's safe to
re-run after adding new transcriptions.

**Output:** one JSON file per document in `entities/`, plus
`entities/consolidated.json` (all entities merged, grouped by type, with
mention counts — this is what powers **Browse by Entity**).

---

## Understanding Contextual Descriptions

Instead of just labeling "John" as a person, Ficherito explains *who John
is in this document*. Across 50 documents, "John" might be the writer's son
in one, a business partner in another, and someone else entirely in a
third — the context field disambiguates these.

Disable it if you just want bare types:

```yaml
processing:
  entity_context: false
```

---

## Customizing Entity Extraction

Edit the `ner_extraction` prompt in `ficherito.yaml` to add domain-specific
guidance. For example, for military records:

```yaml
prompts:
  ner_extraction: |
    You are a historical document analyst specializing in named entity recognition.
    Extract all named entities from this Civil War military document.

    Use these entity types:
    - PERSON: Soldiers, officers, civilians
    - LOCATION: Camps, battlefields, towns
    - DATE: Dates of events
    - ORGANIZATION: Regiments, companies, divisions
    - EVENT: Battles, marches, casualties

    For each entity, explain its role in the document.

    Document text:
    {document_text}

    Return entities as a JSON array:
    [
      {
        "text": "...",
        "type": "...",
        "context": "..."
      }
    ]
```

Keep the JSON array output format — the parser expects `text`, `type`, and
`context` keys per entity.

---

## Entity File Format

**File**: `entities/1863-04-15_page_001.json`

```json
{
  "source_image": "1863-04-15_page_001",
  "extracted_at": "2026-01-15T14:35:00Z",
  "entities": [
    {
      "text": "Sarah",
      "type": "PERSON",
      "context": "Person; the recipient of the letter",
      "positions": [],
      "confidence": null
    }
  ]
}
```

**File**: `entities/consolidated.json`

```json
{
  "total_entities": 3456,
  "unique_texts": 892,
  "by_type": {
    "PERSON": [
      {
        "text": "Sarah",
        "type": "PERSON",
        "contexts": [
          {"document": "1863-04-15_page_001", "context": "Person; the recipient of the letter"}
        ],
        "documents": ["1863-04-15_page_001"],
        "count": 1
      }
    ]
  },
  "all_entities": ["..."]
}
```

---

## Reviewing and Editing Entities

### Edit Directly

```bash
nano entities/1863-04-15_page_001.json
```

Then rebuild the site with `ficherito build` to regenerate
`consolidated.json` from all entity files and pick up your changes.

### Edit via the CMS

Once deployed, collaborators can add/remove/edit entities per document
through Sveltia CMS at `/admin/` instead — see
[Deployment](deployment.md#editing-content-with-sveltia-cms).

### Find a Specific Entity Type

```bash
grep -h '"type": "PERSON"' entities/*.json | sort | uniq -c | sort -rn
```

---

## Browsing Entities on the Site

The built site's **Browse by Entity** page groups entities by type, shows
mention counts, and links each mention back to its document with its
context — built from `entities/consolidated.json`.

---

## Troubleshooting

### No Entities Extracted

- Check the transcription itself first — empty or very short transcriptions
  produce no entities.
- Confirm `processing.extract_entities: true` in `ficherito.yaml`.

### Wrong Entity Types

The LLM sometimes makes mistakes (e.g. "Philadelphia" tagged as PERSON).
Edit the entity JSON file manually, or refine the `ner_extraction` prompt.

### Missing Important Entities

Make the prompt more specific about what to look for — see
[Customizing Entity Extraction](#customizing-entity-extraction) above.

---

## Next Steps

- **[Building Sites](building-sites.md)** - Create your website
- **[Command Reference](../commands/entities.md)** - Full command options
