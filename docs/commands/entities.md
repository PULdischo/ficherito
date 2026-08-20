# ficherito entities

Extract named entities (people, places, dates, organizations, and more) from transcribed documents.

---

## Usage

```bash
ficherito entities [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|--------------|---------|
| `--config` | `-c` | Path to config file | `ficherito.yaml` |
| `--limit` | `-l` | Limit number of documents | all |
| `--concurrency` | `-j` | Concurrent API requests | `10` |

---

## What It Does

1. Reads transcription files from `transcriptions/`
2. Sends each one, concurrently, to the LLM with the `ner_extraction` prompt
3. Saves per-document entity JSON to `entities/`
4. Regenerates `entities/consolidated.json` from **all** entity files (not just newly processed ones)

```
transcriptions/
├── letter_001.md  → entities/letter_001.json
├── letter_002.md  → entities/letter_002.json
└── ...                              → entities/consolidated.json
```

Documents that already have an entity file are skipped, so it's safe to
re-run after adding new transcriptions.

**Prerequisite:** run `ficherito extract` first.

---

## Examples

### Extract All Entities

```bash
ficherito entities
```

### Test on a Subset

```bash
ficherito entities --limit 10
```

---

## Output Format

```json
{
  "source_image": "letter_001",
  "extracted_at": "2026-01-15T10:35:00Z",
  "entities": [
    {
      "text": "John Smith",
      "type": "PERSON",
      "context": "Person; the writer of the letter",
      "positions": [],
      "confidence": null
    }
  ]
}
```

## Entity Types

| Type | Examples |
|------|----------|
| `PERSON` | John Smith, Dr. Wilson |
| `ORGANIZATION` | Congress, First Bank |
| `LOCATION` | Philadelphia, Virginia |
| `DATE` | March 15, 1865, yesterday |
| `MONEY` | $500, fifty dollars |
| `LEGAL_TERM` | plaintiff, defendant, executor |
| `EVENT` | the war, the election |
| `DOCUMENT` | the deed, his will |
| `OCCUPATION` | blacksmith, farmer, attorney |
| `RELATIONSHIP` | my brother, her husband |

---

## Configuration

```yaml
processing:
  extract_entities: true
  entity_context: true   # include role descriptions, not just bare types

prompts:
  ner_extraction: |
    You are a historical document analyst specializing in named entity recognition.
    ...
```

See [Entity Extraction](../usage/entities.md#customizing-entity-extraction)
for how to customize entity types and prompt guidance.

---

## Reviewing and Editing

```bash
# Edit a single document's entities
nano entities/letter_001.json

# Find all PERSON entities across the collection
grep -h '"type": "PERSON"' entities/*.json | sort | uniq -c | sort -rn
```

After editing, run `ficherito build` to regenerate `consolidated.json` and
the site. Once deployed, entities can also be edited through the Sveltia
CMS at `/admin/`.

---

## Troubleshooting

### No Entities Extracted

Check the transcription itself — very short or empty transcriptions
produce no entities. Confirm `processing.extract_entities: true`.

### Wrong Entity Types

The LLM sometimes misclassifies (e.g. "Philadelphia" as PERSON). Edit the
JSON file directly, or refine the `ner_extraction` prompt.

---

## See Also

- **[Named Entity Recognition](../concepts/named-entities.md)** - NER concepts
- **[Entities Usage Guide](../usage/entities.md)** - Practical guide
- **[Configuration](../usage/configuration.md)** - Full configuration reference
