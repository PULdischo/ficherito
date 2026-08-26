# Troubleshooting

Solutions to common issues when using Ficherito.

---

## Installation Issues

### "pip: command not found"

**Solution (macOS/Linux):**
```bash
python3 -m pip install ficherito
```

**Solution (Windows):**
```powershell
py -m pip install ficherito
```

---

### "Could not find a version that satisfies the requirement"

Your Python version may be too old — Ficherito needs 3.10+.

```bash
python --version
```

---

### `npm not found; skipping Eleventy/Pagefind build`

`ficherito build` needs Node.js 20+ for the Eleventy/Pagefind step. Install
it from [nodejs.org](https://nodejs.org/), then re-run `ficherito build`.

---

## API Key Issues

### "OPENAI_API_KEY not set"

**Solution:**

1. Create `.env` if it doesn't exist:
```bash
cp .env.example .env
```

2. Add your key:
```bash
# .env
OPENAI_API_KEY=sk-your-actual-key-here
```

3. Verify:
```bash
ficherito validate
```

---

### "Invalid API key" / 401 Unauthorized

**Check:**
1. The key is correct (no extra spaces)
2. The key is active and matches the endpoint in `OPENAI_BASE_URL`
3. You're using the right variable name (`OPENAI_API_KEY`, not the old `DASHSCOPE_API_KEY`)

---

### Rate Limit Exceeded (429)

**Solution:**

```bash
ficherito extract --concurrency 3
```

Lower `--concurrency` on `extract` or `entities` if you're hitting your
provider's rate limits.

---

## Transcription Issues

### Empty Transcriptions

**Possible causes:**
1. Image quality too low
2. The image isn't a text document
3. A transient API error

**Solutions:**

1. Check the source image is legible and correctly oriented.
2. Retry with a more specific prompt:
```yaml
prompts:
  text_extraction: |
    This document may be faded or damaged.
    Transcribe any visible text, noting unclear sections.
```

---

### Truncated Transcriptions

If a transcription stops mid-page — common with multi-page images (e.g. two
pages of a diary scanned into one photo) — the model likely hit its output
token limit before finishing. Check the log for:

```
HTR response truncated at max_tokens=...
```

**Solution:** raise `processing.max_output_tokens` in `ficherito.yaml`
(default: 4096) and re-run `ficherito extract`:

```yaml
processing:
  max_output_tokens: 8192
```

---

### Wrong Language Detected

```yaml
prompts:
  text_extraction: |
    This is a document written in German.
    Transcribe all text in German, preserving original spelling.
```

---

### Low Confidence Scores

```bash
grep -l "confidence: 0.[0-6]" transcriptions/*.md
```

Historical handwriting is genuinely hard — treat low confidence as a
signal to review the source image, not necessarily an error.

---

## Entity Issues

### No Entities Extracted

```
Extracted entities from 0 documents
```

**Check:**
1. `processing.extract_entities: true` in `ficherito.yaml`
2. Transcriptions aren't empty:
```bash
cat transcriptions/sample.md
```
3. The log for a truncated response (`Entity extraction response truncated
   at max_tokens=...`) — a cut-off response can't be parsed as valid JSON,
   so it silently yields zero entities. Raise `processing.max_output_tokens`
   (see [Truncated Transcriptions](#truncated-transcriptions) above) and
   re-run `ficherito entities`.

---

### Wrong Entity Types

The LLM sometimes misclassifies (e.g. "Philadelphia" tagged as PERSON).
Edit `entities/<id>.json` directly, or refine `prompts.ner_extraction` —
see [Entity Extraction](../usage/entities.md#customizing-entity-extraction).

---

## Build Issues

### "Site directory not found" (from `ficherito serve`)

Run `ficherito build` first.

### Search Not Working

```bash
ls site/_site/pagefind/
```

If missing: confirm `website.enable_search: true`, that Node.js is
installed, and rebuild.

### Missing Images on the Site

Ficherito looks for `images/<id>.{jpg,jpeg,png,tiff,webp}` (or
`data/images/<id>.*`) to compress and copy into the site. Confirm the
filename stem matches the document ID:

```bash
ls site/src/assets/images/documents/
```

### Eleventy Build Failed

Run it directly for the full error output:

```bash
cd site
npm run build
```

Common cause: a hand-edited `.njk` template with a syntax error.

---

## Performance

### Processing Slow

```bash
ficherito process --concurrency 20 --batch-size 100
```

Increase gradually and watch for rate-limit errors.

### Out of Memory

```bash
ficherito process --batch-size 10
```

Lower `--batch-size` to hold fewer images in memory at once.

---

## Getting Help

### Gather Diagnostic Info

```bash
python --version
node --version
pip show ficherito
ficherito validate
```

### Ask for Help

1. Check this documentation — most issues are covered
2. Search [GitHub issues](https://github.com/PULdischo/ficherito/issues)
3. Open a new issue with the diagnostic info above

---

## See Also

- **[FAQ](faq.md)** - Frequently asked questions
- **[Glossary](glossary.md)** - Terms and definitions
- **[Configuration](../usage/configuration.md)** - Configuration reference
