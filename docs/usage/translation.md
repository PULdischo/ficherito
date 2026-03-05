# Translation

This guide covers translating transcribed documents to other languages.

---

## Overview

Flatfish can automatically translate your transcribed documents using Google Translate. This is particularly useful for:

- **Multilingual archives** - Making documents accessible to researchers who don't read the original language
- **Spanish colonial records** - Translating historical Spanish documents to English
- **International collections** - Providing translations alongside originals

---

## Enabling Translation

Add the `translate` section to your `flatfish.yaml`:

```yaml
translate:
  enabled: true
  source_languages:
    - "es"
  target_language: "en"
  default_tab: "translation"
```

---

## Configuration Options

### enabled

Enable or disable translation. Set to `false` to skip translation entirely.

```yaml
translate:
  enabled: true  # or false
```

### source_languages

A list of source languages your documents are written in. Use [ISO 639-1 language codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).

```yaml
translate:
  source_languages:
    - "es"      # Spanish
    - "pt"      # Portuguese
```

You can also use `"auto"` for automatic language detection:

```yaml
translate:
  source_languages:
    - "auto"
```

### target_language

The language to translate documents into:

```yaml
translate:
  target_language: "en"  # English
```

### default_tab

Which tab to show by default on document pages:

```yaml
translate:
  default_tab: "translation"   # Show translation first
  # or
  default_tab: "transcription" # Show original first
```

---

## Running Translation

Once configured, run the translate command:

```bash
flatfish translate
```

### Progress Output

```
Validating language codes...
  Source: ['es'] ✓
  Target: en ✓

⠋ Translating 1234/5000 (skipped 0)...

✓ Translation complete!
  Translated: 4990
  Skipped: 0
  Errors: 10
```

### Command Options

```bash
# Translate a limited number of documents (for testing)
flatfish translate --limit 10

# Force re-translation of all documents
flatfish translate --force

# Override source language
flatfish translate --source auto
```

---

## Translation Files

Translations are saved alongside your transcriptions:

```
your-project/
├── transcriptions/
│   ├── document_001.md
│   ├── document_002.md
│   └── ...
├── translations/
│   ├── document_001.md   # Translated version
│   ├── document_002.md
│   └── ...
```

---

## Website Display

After building your site, each document page will display tabs for switching between the original transcription and translation.

The `default_tab` setting controls which appears first.

---

## Common Language Pairs

### Spanish → English

For Spanish colonial documents, missionary records, etc.:

```yaml
translate:
  enabled: true
  source_languages:
    - "es"
  target_language: "en"
  default_tab: "translation"
```

### French → English

For French historical documents:

```yaml
translate:
  enabled: true
  source_languages:
    - "fr"
  target_language: "en"
  default_tab: "transcription"
```

### Multiple Languages

For collections with documents in multiple languages:

```yaml
translate:
  enabled: true
  source_languages:
    - "es"
    - "pt"
    - "fr"
  target_language: "en"
  default_tab: "translation"
```

---

## Handling Errors

### Character Limit

Google Translate has a 5,000 character limit per request. Documents exceeding this will show an error:

```
Error translating document_001: Text length need to be between 0 and 5000 characters
```

**Solution**: These documents are skipped automatically. You may need to manually translate very long documents.

### Rate Limiting

If you're translating many documents quickly, you may encounter rate limiting:

```
Error translating document_001: Rate limit exceeded
```

**Solution**: Wait a few minutes and re-run with `--force` to retry failed documents.

---

## Quality Considerations

Machine translation has limitations:

- **Historical language** - Archaic spellings and grammar may not translate well
- **Specialized terminology** - Legal, medical, or technical terms may be mistranslated
- **Context** - Some nuances may be lost in translation

```{tip}
Consider translation as an **accessibility aid** rather than a scholarly replacement. Always provide access to the original transcription alongside translations.
```

---

## Full Pipeline

Translation fits into the Flatfish pipeline after transcription:

```bash
# Full pipeline
flatfish extract     # Extract text from images
flatfish entities    # Extract named entities  
flatfish translate   # Translate to target language
flatfish summarize   # Generate summaries
flatfish build       # Build website with translations
```

Or run everything at once:

```bash
flatfish process
```

---

## Next Steps

- **[Building Sites](building-sites.md)** - Include translations in your website
- **[Configuration](configuration.md)** - Full configuration reference
- **[Transcription](transcription.md)** - Extracting text from images
