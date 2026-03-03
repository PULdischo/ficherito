# API Reference

Python API documentation for using Flatfish programmatically.

---

## Overview

While Flatfish is primarily a CLI tool, you can also use it as a Python library:

```python
from flatfish import Pipeline, Config
from flatfish.summary import QwenSummarizer
from flatfish.transcription import transcribe_document
from flatfish.entities import extract_entities
```

---

## Quick Start

```python
from flatfish import Pipeline

# Load configuration
pipeline = Pipeline.from_config("flatfish.yaml")

# Run full pipeline
results = pipeline.process()

# Or run specific steps
pipeline.transcribe()
pipeline.extract_entities()
pipeline.summarize()
pipeline.combine()
pipeline.build()
```

---

## Core Classes

### Pipeline

Main orchestration class.

```python
from flatfish import Pipeline

class Pipeline:
    """Orchestrates the document processing pipeline."""
    
    @classmethod
    def from_config(cls, config_path: str) -> "Pipeline":
        """Load pipeline from configuration file."""
        
    def process(self, steps: list[str] = None) -> dict:
        """Run pipeline steps.
        
        Args:
            steps: Specific steps to run. If None, runs all.
                   Options: ['transcribe', 'entities', 'summarize', 
                            'combine', 'build']
        
        Returns:
            dict with results from each step
        """
        
    def transcribe(self, force: bool = False) -> list[dict]:
        """Transcribe all documents."""
        
    def extract_entities(self, force: bool = False) -> list[dict]:
        """Extract entities from transcriptions."""
        
    def summarize(self, force: bool = False) -> dict:
        """Generate batch summaries."""
        
    def combine(self) -> dict:
        """Combine batch summaries into final outputs."""
        
    def build(self, force: bool = False) -> None:
        """Build static site."""
```

#### Example

```python
from flatfish import Pipeline

# Initialize
pipeline = Pipeline.from_config("flatfish.yaml")

# Run with progress callback
def on_progress(step, current, total):
    print(f"{step}: {current}/{total}")

results = pipeline.process(on_progress=on_progress)

# Access results
print(f"Transcribed: {len(results['transcriptions'])} documents")
print(f"Entities: {results['entities']['total']}")
```

---

### Config

Configuration management.

```python
from flatfish import Config

class Config:
    """Manages Flatfish configuration."""
    
    @classmethod
    def load(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create configuration from dictionary."""
        
    def save(self, path: str) -> None:
        """Save configuration to file."""
        
    # Properties
    project: ProjectConfig
    source: SourceConfig
    processing: ProcessingConfig
    summary: SummaryConfig
    site: SiteConfig
```

#### Example

```python
from flatfish import Config

# Load existing config
config = Config.load("flatfish.yaml")

# Modify settings
config.processing.batch_size = 30
config.summary.model = "qwen-vl-max"

# Save changes
config.save("flatfish.yaml")

# Create from scratch
config = Config.from_dict({
    "project": {"name": "My Collection"},
    "processing": {"batch_size": 20}
})
```

---

## Transcription

### transcribe_document

Transcribe a single document.

```python
from flatfish.transcription import transcribe_document

async def transcribe_document(
    image_path: str,
    model: str = "qwen-vl-max",
    prompt: str = None,
    api_key: str = None
) -> dict:
    """Transcribe a document image.
    
    Args:
        image_path: Path to image file
        model: Model to use
        prompt: Custom extraction prompt
        api_key: API key (uses env if not provided)
    
    Returns:
        dict with 'raw_text', 'cleaned_text', 'confidence'
    """
```

#### Example

```python
import asyncio
from flatfish.transcription import transcribe_document

async def main():
    result = await transcribe_document(
        "images/letter_001.jpg",
        prompt="Transcribe this 19th-century letter..."
    )
    print(result['cleaned_text'])
    print(f"Confidence: {result['confidence']}")

asyncio.run(main())
```

### transcribe_batch

Transcribe multiple documents.

```python
from flatfish.transcription import transcribe_batch

async def transcribe_batch(
    image_paths: list[str],
    batch_size: int = 20,
    **kwargs
) -> list[dict]:
    """Transcribe multiple documents.
    
    Args:
        image_paths: List of image paths
        batch_size: Images per API call
        **kwargs: Passed to transcribe_document
    
    Returns:
        List of transcription results
    """
```

---

## Entity Extraction

### extract_entities

Extract entities from text.

```python
from flatfish.entities import extract_entities

def extract_entities(
    text: str,
    model: str = "en_core_web_lg",
    entity_types: list[str] = None,
    min_confidence: float = 0.7
) -> list[dict]:
    """Extract named entities from text.
    
    Args:
        text: Input text
        model: spaCy model name
        entity_types: Types to extract (None = all)
        min_confidence: Minimum confidence threshold
    
    Returns:
        List of entity dicts with 'text', 'label', 
        'start', 'end', 'confidence'
    """
```

#### Example

```python
from flatfish.entities import extract_entities

text = "John Smith traveled to Philadelphia on March 15, 1865."

entities = extract_entities(text)
for entity in entities:
    print(f"{entity['text']}: {entity['label']}")
    
# Output:
# John Smith: PERSON
# Philadelphia: GPE
# March 15, 1865: DATE
```

### EntityExtractor

Class-based entity extraction.

```python
from flatfish.entities import EntityExtractor

class EntityExtractor:
    """Configurable entity extractor."""
    
    def __init__(
        self,
        model: str = "en_core_web_lg",
        custom_entities: dict = None
    ):
        """Initialize extractor.
        
        Args:
            model: spaCy model name
            custom_entities: Custom entity patterns
        """
        
    def extract(self, text: str) -> list[dict]:
        """Extract entities from text."""
        
    def extract_batch(self, texts: list[str]) -> list[list[dict]]:
        """Extract entities from multiple texts."""
```

---

## Summarization

### QwenSummarizer

Main summarization class.

```python
from flatfish.summary import QwenSummarizer

class QwenSummarizer:
    """Track-based document summarizer."""
    
    def __init__(
        self,
        config: Config,
        api_key: str = None
    ):
        """Initialize summarizer.
        
        Args:
            config: Flatfish configuration
            api_key: DashScope API key
        """
        
    async def summarize(
        self,
        transcriptions: list[dict],
        output_dir: str = "batches/"
    ) -> dict:
        """Generate batch summaries for all tracks.
        
        Args:
            transcriptions: List of transcription dicts
            output_dir: Directory for batch files
        
        Returns:
            dict with paths to generated files
        """
        
    async def combine(
        self,
        batches_dir: str = "batches/",
        output_dir: str = "output/"
    ) -> dict:
        """Combine batch summaries into final outputs.
        
        Args:
            batches_dir: Directory with batch files
            output_dir: Directory for final outputs
        
        Returns:
            dict with paths to final files
        """
        
    def save_summary(
        self,
        summary: dict,
        output_dir: str = "output/"
    ) -> None:
        """Save summary to editable text files."""
        
    def load_summary(
        self,
        output_dir: str = "output/"
    ) -> dict:
        """Load summary from text or JSON files."""
```

#### Example

```python
import asyncio
from flatfish import Config
from flatfish.summary import QwenSummarizer

async def main():
    config = Config.load("flatfish.yaml")
    summarizer = QwenSummarizer(config)
    
    # Load transcriptions
    transcriptions = load_transcriptions("transcriptions/")
    
    # Generate summaries
    batch_results = await summarizer.summarize(transcriptions)
    
    # Combine into final outputs
    final_results = await summarizer.combine()
    
    print(f"Timeline: {final_results['timeline']}")
    print(f"Key Changes: {final_results['key_changes']}")

asyncio.run(main())
```

---

## Site Building

### SiteBuilder

Generate static site.

```python
from flatfish.site import SiteBuilder

class SiteBuilder:
    """Static site generator."""
    
    def __init__(
        self,
        config: Config,
        template_dir: str = None
    ):
        """Initialize builder.
        
        Args:
            config: Flatfish configuration
            template_dir: Custom template directory
        """
        
    def build(
        self,
        output_dir: str = "site/",
        force: bool = False
    ) -> dict:
        """Build static site.
        
        Args:
            output_dir: Output directory
            force: Rebuild all pages
        
        Returns:
            dict with build statistics
        """
        
    def render_template(
        self,
        template_name: str,
        context: dict
    ) -> str:
        """Render a single template."""
```

---

## Utilities

### File Operations

```python
from flatfish.utils import (
    load_json,
    save_json,
    load_transcriptions,
    ensure_directory
)

# Load JSON file
data = load_json("transcriptions/letter_001.json")

# Save JSON file
save_json(data, "output/result.json")

# Load all transcriptions
transcriptions = load_transcriptions("transcriptions/")

# Ensure directory exists
ensure_directory("output/summaries/")
```

### Progress Tracking

```python
from flatfish.utils import ProgressTracker

tracker = ProgressTracker(total=100)

for i in range(100):
    # Do work
    tracker.update(1)
    print(tracker.progress_bar())
```

---

## Error Handling

### Exceptions

```python
from flatfish.exceptions import (
    FlatfishError,
    ConfigError,
    APIError,
    TranscriptionError,
    EntityError,
    SummaryError,
    BuildError
)

try:
    pipeline.process()
except ConfigError as e:
    print(f"Configuration error: {e}")
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
except FlatfishError as e:
    print(f"General error: {e}")
```

---

## Async Support

Most operations are async-compatible:

```python
import asyncio
from flatfish import Pipeline

async def main():
    pipeline = Pipeline.from_config("flatfish.yaml")
    
    # Async processing
    await pipeline.transcribe_async()
    await pipeline.summarize_async()
    await pipeline.combine_async()

asyncio.run(main())
```

---

## Type Hints

Full type annotations available:

```python
from flatfish.types import (
    TranscriptionResult,
    EntityResult,
    SummaryResult,
    BatchResult
)

def process_transcription(result: TranscriptionResult) -> None:
    text: str = result['cleaned_text']
    confidence: float = result['confidence']
```

---

## See Also

- **[Configuration Guide](../usage/configuration.md)** - Configuration reference
- **[Commands Overview](../commands/overview.md)** - CLI reference
- **[Pipeline Concepts](../concepts/pipeline.md)** - How the pipeline works
