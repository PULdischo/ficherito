# Python Usage

Ficherito is primarily a CLI tool. There's no separate, stabilized public
Python API — but since it's a regular installed package, you can import and
call the same functions the CLI commands themselves use.

```{note}
These are internal functions, not a versioned public API — signatures may
change between releases. For scripting Ficherito, prefer shelling out to
the CLI (`subprocess`) unless you specifically need Python-level access.
```

---

## Configuration

```python
from ficherito.config import load_config, load_env, FicheritoConfig

config: FicheritoConfig = load_config()          # reads ./ficherito.yaml
env = load_env()                                   # reads ./.env

print(config.dataset.images_dir)
print(env.api_key is not None)
```

---

## Running the Pipeline

```python
from ficherito.config import load_config, load_env
from ficherito.pipeline import run_pipeline

config = load_config()
env = load_env()

run_pipeline(
    config=config,
    env=env,
    limit=20,
    max_concurrent=10,
    batch_size=50,
    skip_entities=False,
    skip_build=False,
    verbose=True,
)
```

### Individual Stages

```python
from ficherito.pipeline import run_extraction, run_entity_extraction

run_extraction(config, env, limit=20, max_concurrent=10)
run_entity_extraction(config, env, limit=20, max_concurrent=10)
```

---

## Working with Images

```python
from ficherito.dataset import list_image_files, iter_document_images

files = list_image_files(config)                        # sorted list of Path
for doc in iter_document_images(config, limit=10):
    print(doc.image_id, doc.filename, doc.date)
```

---

## Transcription

```python
from ficherito.htr.engine import HTREngine, load_transcription

engine = HTREngine(config, env=env)
# engine.extract_batch_async(...) — see src/ficherito/htr/engine.py

text, metadata = load_transcription("transcriptions/letter_001.md")
```

---

## Entities

```python
from ficherito.entities.extractor import (
    EntityExtractor,
    load_entities,
    consolidate_entities,
)

result = load_entities("entities/letter_001.json")
for entity in result.entities:
    print(entity.text, entity.type, entity.context)

consolidated = consolidate_entities([result])   # by_type / all_entities dict
```

---

## Translation

```python
from ficherito.translation import Translator, validate_languages

is_valid, error = validate_languages(["es"], "en")
translator = Translator(config=config)
result = translator.translate_document("letter_001", text, "es")
```

---

## Site Building

```python
from ficherito.site.builder import build_site

site_dir = build_site(config, base_url="/", enable_search=True)
```

This emits content into `site/src/` and shells out to `npm run build`
inside it (Eleventy + Pagefind) — see [Building Sites](../usage/building-sites.md)
for what that does under the hood.

---

## Dates

```python
from ficherito.utils.dates import (
    extract_date_from_filename,
    sort_by_date,
    format_date_display,
)

date = extract_date_from_filename("1863-04-15_page1.jpg")   # "1863-04-15"
format_date_display(date)                                     # "April 15, 1863"
```

Dates are modeled with [undate](https://github.com/dh-tech/undate-python)
to support partial precision (year-only, year-month, or full day).

---

## See Also

- **[Configuration Guide](../usage/configuration.md)** - Configuration reference
- **[Commands Overview](../commands/overview.md)** - CLI reference
- **[Pipeline Concepts](../concepts/pipeline.md)** - How the pipeline works
