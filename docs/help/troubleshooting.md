# Troubleshooting

Solutions to common issues when using Flatfish.

---

## Installation Issues

### "pip: command not found"

Python may not be in your PATH.

**Solution (macOS/Linux):**
```bash
# Use python3 explicitly
python3 -m pip install flatfish

# Or add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

**Solution (Windows):**
```powershell
# Use py launcher
py -m pip install flatfish
```

---

### "Could not find a version that satisfies the requirement"

Your Python version may be too old.

**Check version:**
```bash
python --version
# Need 3.9+
```

**Solution:**
```bash
# Install Python 3.11
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11

# Windows: Download from python.org
```

---

### NumPy/Pandas compatibility errors

```
ValueError: numpy.dtype size changed, may indicate binary incompatibility
```

**Solution:**
```bash
pip install numpy==1.26.4
pip install --force-reinstall pandas
```

---

### spaCy model download fails

```
OSError: [E050] Can't find model 'en_core_web_lg'
```

**Solution:**
```bash
python -m spacy download en_core_web_lg

# If permission error
python -m spacy download en_core_web_lg --user
```

---

## API Key Issues

### "API key not found"

```
Error: DASHSCOPE_API_KEY not set
```

**Solution:**

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Add your key:
```bash
# .env
DASHSCOPE_API_KEY=sk-your-actual-key-here
```

3. Verify:
```bash
echo $DASHSCOPE_API_KEY
# Should show your key
```

---

### "Invalid API key"

```
Error: 401 Unauthorized - Invalid API key
```

**Check:**
1. Key is correct (no extra spaces)
2. Key is active (not expired)
3. Key has correct permissions

**Get new key:**
1. Go to [DashScope Console](https://dashscope.console.aliyun.com/)
2. Navigate to API Keys
3. Generate new key
4. Update `.env`

---

### "Rate limit exceeded"

```
Error: 429 Too Many Requests
```

**Solution:**
```yaml
# flatfish.yaml
processing:
  retry_count: 5
  retry_delay: 60  # Wait longer between retries
  max_concurrent: 2  # Reduce parallel calls
```

Or wait and retry:
```bash
# Wait a few minutes, then
flatfish process --resume
```

---

## Transcription Issues

### Empty transcriptions

Documents return blank or minimal text.

**Possible causes:**
1. Image quality too low
2. Document is not text (e.g., photograph)
3. API processing error

**Solutions:**

1. **Check image quality:**
```bash
# View image info
identify image.jpg
# Should be 300+ DPI, readable size
```

2. **Improve image:**
```bash
# Increase contrast
convert image.jpg -contrast-stretch 2%x1% improved.jpg
```

3. **Retry with custom prompt:**
```yaml
prompts:
  text_extraction: |
    This document may be faded or damaged.
    Transcribe any visible text, noting unclear sections.
```

---

### Wrong language detection

Model transcribes in wrong language.

**Solution:**
```yaml
prompts:
  text_extraction: |
    This is a document written in German.
    Transcribe all text in German, preserving original spelling.
```

---

### Low confidence scores

Many documents have confidence < 0.7.

**Check:**
```bash
# Find low-confidence files
grep -l '"confidence": 0\.[0-6]' transcriptions/*.json | wc -l
```

**Solutions:**

1. **Review sample images** - May be genuinely difficult
2. **Adjust expectations** - Historical handwriting is hard
3. **Mark for manual review:**
```bash
# Create review list
grep -l '"confidence": 0\.[0-6]' transcriptions/*.json > review_list.txt
```

---

## Summarization Issues

### "Context length exceeded"

```
Error: 400 Bad Request - Context length exceeded
```

**Cause:** Too much text for single API call.

**Solution:**
```yaml
# flatfish.yaml
summary:
  max_combine_chars: 60000  # Reduce from 80000
  batch_group_size: 30       # Reduce from 50
```

---

### Summaries too short

Final summaries lack detail.

**Solutions:**

1. **Increase context limit:**
```yaml
summary:
  max_combine_chars: 100000
```

2. **Improve combine prompts:**
```yaml
prompts:
  combine_timeline: |
    IMPORTANT: Preserve all specific dates, names, and events.
    Do not over-summarize.
    
    Combine these timeline sections...
```

3. **Use smaller batch groups:**
```yaml
summary:
  batch_group_size: 25  # More granular combining
```

---

### Hallucinated content

AI generates facts not in documents.

**Solutions:**

1. **Add grounding instruction:**
```yaml
prompts:
  timeline: |
    Only include events explicitly mentioned in the documents.
    Do not infer or assume additional details.
    If uncertain, note "[unclear]".
```

2. **Review and correct** - Use editable output files:
```bash
# Edit output files
code output/timeline.txt
```

---

### Batch files not found

```
Error: No batch files found in batches/
```

**Check:**
```bash
ls batches/
# Should show timeline/, key_changes/, etc.
```

**Solution:**
Run summarize first:
```bash
flatfish summarize
flatfish combine
```

---

## Entity Issues

### No entities extracted

```
Complete: 500/500 documents
Total entities: 0
```

**Possible causes:**
1. Transcriptions empty
2. spaCy model not loaded
3. Text preprocessing issue

**Solutions:**

1. **Check transcriptions:**
```bash
cat transcriptions/sample.json | jq '.cleaned_text'
```

2. **Verify spaCy:**
```python
import spacy
nlp = spacy.load("en_core_web_lg")
doc = nlp("John Smith went to Philadelphia.")
print([(ent.text, ent.label_) for ent in doc.ents])
```

---

### Too many false positives

Common words marked as entities.

**Solutions:**

1. **Increase confidence threshold:**
```yaml
entities:
  min_confidence: 0.85
```

2. **Filter entity types:**
```yaml
entities:
  types:
    - PERSON
    - GPE
    - DATE
    # Remove less reliable types
```

---

## Build Issues

### Template errors

```
Error: Template 'document.html' not found
```

**Solution:**
```bash
# Use default template
flatfish build --template default

# Or check custom template path
ls templates/document.html
```

---

### Missing images in site

Document images don't appear.

**Check config:**
```yaml
site:
  images:
    include: true
    # Or link to external
    external_url: "https://example.com/images/"
```

---

## Performance Issues

### Processing very slow

**Solutions:**

1. **Increase batch size:**
```yaml
processing:
  batch_size: 30
```

2. **Increase parallelism:**
```yaml
processing:
  max_concurrent: 8
```

3. **Skip unnecessary steps:**
```yaml
processing:
  skip:
    - entities  # If not needed
```

---

### Out of memory

```
MemoryError: Unable to allocate...
```

**Solutions:**

1. **Reduce batch size:**
```yaml
processing:
  batch_size: 10
```

2. **Process in chunks:**
```bash
# Process subsets
flatfish process --limit 100
flatfish process --skip 100 --limit 100
```

---

## Getting Help

### Gather diagnostic info

```bash
# System info
python --version
pip show flatfish

# Config
cat flatfish.yaml

# Recent errors
tail -50 .flatfish/flatfish.log
```

### Ask for help

1. **Check documentation** - Most issues are covered
2. **Search GitHub issues** - Similar problems may be solved
3. **Open new issue** - Include diagnostic info above

---

## See Also

- **[FAQ](faq.md)** - Frequently asked questions
- **[Glossary](glossary.md)** - Terms and definitions
- **[Configuration](../usage/configuration.md)** - Configuration reference
