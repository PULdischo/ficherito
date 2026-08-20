# Named Entity Recognition

Learn how Ficherito identifies people, places, dates, and other important entities in your documents.

---

## What is NER?

**Named Entity Recognition (NER)** is the process of identifying and categorizing key information in text:

```
"John Smith traveled to Philadelphia on March 15, 1865."
 └── PERSON ──┘          └── LOCATION ┘  └── DATE ──────┘
```

NER turns unstructured text into structured data that can be browsed and searched.

---

## Entity Types

Ficherito's `ner_extraction` prompt recognizes these types:

| Type | Examples |
|------|----------|
| `PERSON` | John Smith, Mrs. Wilson, General Grant |
| `LOCATION` | Philadelphia, Mississippi River, home |
| `ORGANIZATION` | Congress, First National Bank |
| `DATE` | March 15, 1865, yesterday, next week |
| `MONEY` | $5.00, fifty dollars, 3 shillings |
| `EVENT` | the war, harvest, election |
| `DOCUMENT` | the deed, his will, this letter |
| `LEGAL_TERM` | plaintiff, defendant, executor |
| `OCCUPATION` | blacksmith, farmer, attorney |
| `RELATIONSHIP` | my brother, her husband, the children |

You can add or change types by editing the `ner_extraction` prompt in
`ficherito.yaml` — see [Entity Extraction](../usage/entities.md#customizing-entity-extraction).

---

## How It Works in Ficherito

```
┌─────────────────┐
│ Transcribed     │
│ Document Text   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM extraction  │  The `ner_extraction` prompt asks the model
│ (same endpoint  │  to find entities and (optionally) explain
│  as HTR)        │  each one's role in this specific document
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Per-document    │  entities/<id>.json
│ Entity File     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Consolidation   │  Group by (text, type) across all documents,
│                 │  track mention counts and per-document contexts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ consolidated    │  entities/consolidated.json
│ .json           │  → powers Browse by Entity
└─────────────────┘
```

Unlike a classic NER pipeline, there's no separate span-detection /
classification / coreference-resolution stage — the LLM does extraction
and contextual description together in one call per document, guided by
the prompt.

---

## Entity Output Format

**Per-document** (`entities/1865-03-15_letter.json`):

```json
{
  "source_image": "1865-03-15_letter",
  "extracted_at": "2026-01-15T14:35:00Z",
  "entities": [
    {
      "text": "John Smith",
      "type": "PERSON",
      "context": "Person; the writer of the letter",
      "positions": [],
      "confidence": null
    },
    {
      "text": "Philadelphia",
      "type": "LOCATION",
      "context": "Location; where the writer traveled to",
      "positions": [],
      "confidence": null
    }
  ]
}
```

**Consolidated** (`entities/consolidated.json`), grouped by type with
mention counts and contexts across every document:

```json
{
  "total_entities": 3456,
  "unique_texts": 892,
  "by_type": {
    "PERSON": [
      {
        "text": "John Smith",
        "type": "PERSON",
        "contexts": [
          {"document": "1865-03-15_letter", "context": "Person; the writer of the letter"}
        ],
        "documents": ["1865-03-15_letter"],
        "count": 1
      }
    ]
  },
  "all_entities": ["..."]
}
```

---

## Challenges with Historical Text

### Spelling Variations

```
"Jno. Smith"     → John Smith
"J. Smith Esq."  → John Smith
"Mr Smith"       → John Smith
"John Smyth"     → John Smith (or a different person?)
```

Ficherito doesn't automatically normalize these — the LLM will often
resolve obvious abbreviations in context, but distinct spellings can still
end up as separate entities in `consolidated.json`. Correct these by
editing the entity JSON files directly (or via the CMS) and rebuilding.

### Context Dependency

The same word can be a different entity type depending on context:

```
"Washington" → George Washington (PERSON)
"Washington" → Washington, D.C. (LOCATION)
"Washington" → the Washington regiment (ORGANIZATION)
```

The `entity_context` field — a short phrase explaining the entity's role in
*that specific document* — is what disambiguates these on the site.

---

## Improving Entity Extraction

### Give the Prompt More Guidance

```yaml
prompts:
  ner_extraction: |
    You are a historical document analyst specializing in named entity recognition.
    Extract all named entities from the following transcribed document text.

    Pay special attention to:
    - All people mentioned, even by nickname or title
    - Place names, including informal references
    - Any dates, even relative ones like "last week"

    Document text:
    {document_text}

    Return entities as a JSON array:
    [
      {"text": "...", "type": "...", "context": "..."}
    ]
```

### Manual Review and Correction

1. Extract entities with `ficherito entities`
2. Review `entities/*.json` (or edit via the Sveltia CMS once deployed)
3. Correct misidentified entities, fix types, improve context text
4. Re-run `ficherito build` to regenerate `consolidated.json` and the site

---

## Using Entity Data

The built site's **Browse by Entity** page groups entities by type, shows
mention counts, and links each mention to its document with its context —
built entirely from `entities/consolidated.json`. There's no separate
network-graph or geographic-mapping feature currently; those would need to
be built from the same consolidated JSON if you want them.

---

## Best Practices

1. **Start with automatic extraction**, then refine — don't hand-author entities from scratch.
2. **Review high-value documents first** — important documents, or ones with many entities.
3. **Keep a mental list of your collection's recurring people/places** so you can spot mis-extractions quickly.
4. **Rebuild after every edit** (`ficherito build`) so `consolidated.json` and the site stay in sync.

---

## Next Steps

- **[Entity Extraction Usage Guide](../usage/entities.md)** - Practical how-to
- **[HTR and OCR](htr-ocr.md)** - How transcription works
