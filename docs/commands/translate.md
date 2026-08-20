# translate

Translate transcriptions to a target language using Google Translate.

---

## Synopsis

```bash
ficherito translate [OPTIONS]
```

---

## Description

The `translate` command processes all transcription files and translates them from the source language(s) to a target language using Google Translate via the `deep_translator` library.

Translations are saved as individual markdown files in the `translations/` directory (or as configured in `output.translations_dir`).

---

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Path to config file (default: `ficherito.yaml`) |
| `--limit` | `-l` | Limit number of documents to translate |
| `--force` | `-f` | Force re-translation even if translation exists |
| `--source` | `-s` | Override source language (default: from config or 'auto') |

---

## Examples

### Basic Translation

Translate all transcriptions using settings from config:

```bash
ficherito translate
```

### Test with a Few Documents

Translate only the first 10 documents:

```bash
ficherito translate --limit 10
```

### Force Re-translation

Re-translate all documents, even if translations already exist:

```bash
ficherito translate --force
```

### Override Source Language

Translate from a specific source language:

```bash
ficherito translate --source es
```

---

## Configuration

The translate command uses settings from the `translate:` section of `ficherito.yaml`:

```yaml
translate:
  # Enable/disable translation
  enabled: true
  
  # Source language(s) - ISO 639-1 codes
  # Use "auto" for automatic detection
  source_languages:
    - "es"
    - "pt"
  
  # Target language - ISO 639-1 code
  target_language: "en"
  
  # Which tab to show by default on document pages
  # Options: "transcription" or "translation"
  default_tab: "translation"
```

---

## Language Codes

Common language codes (ISO 639-1):

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `pt` | Portuguese |
| `it` | Italian |
| `nl` | Dutch |
| `ru` | Russian |
| `zh-CN` | Chinese (Simplified) |
| `ja` | Japanese |
| `ko` | Korean |
| `ar` | Arabic |
| `auto` | Auto-detect |

For a complete list of supported languages, run:

```bash
ficherito translate --help
```

Or check the [Google Translate supported languages](https://cloud.google.com/translate/docs/languages).

---

## Output

Translations are saved as markdown files:

```
translations/
├── document_001.md
├── document_002.md
├── document_003.md
└── ...
```

Each file contains the translated text in the target language.

---

## Limitations

- **Character limit**: Google Translate has a 5,000 character limit per request. Documents exceeding this limit will show an error and be skipped.
- **Rate limiting**: Google Translate may rate-limit requests. The command handles this gracefully with retries.
- **Quality**: Machine translation quality varies by language pair and document type.

---

## Website Integration

When translations are available, document pages display tabs to switch between:

- **Original** - The original transcription
- **Translation** - The translated text

The `default_tab` setting in your config controls which tab is shown first.

---

## See Also

- **[Configuration](../usage/configuration.md)** - Full configuration reference
- **[Extract](extract.md)** - Extracting text from images
- **[Building Sites](../usage/building-sites.md)** - Generate the website with translations
