"""Configuration loading and validation for Flatfish."""

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatasetConfig(BaseModel):
    """Configuration for HuggingFace dataset."""

    source: str = Field(..., description="HuggingFace dataset address (e.g., 'username/dataset')")
    splits: list[str] = Field(default=["train"], description="Dataset splits to load")
    image_column: str = Field(default="image", description="Column name containing images")
    name_column: Optional[str] = Field(default=None, description="Optional column containing original filename or document name")


class ProcessingConfig(BaseModel):
    """Configuration for document processing."""

    extract_entities: bool = Field(default=True, description="Enable entity extraction")
    entity_context: bool = Field(default=True, description="Include contextual descriptions")


class PromptsConfig(BaseModel):
    """Prompts for LLM operations."""

    text_extraction: str = Field(
        default="""You are a historical document transcription assistant. Given the raw OCR/HTR 
output from a handwritten document, clean up and correct the text while:

1. Preserving the original spelling, including archaic forms
2. Fixing obvious OCR errors (e.g., 'tbe' → 'the')
3. Maintaining original line breaks where meaningful
4. Preserving original punctuation style
5. Marking unclear or illegible portions with [?] or [illegible]
6. Expanding common abbreviations only if unambiguous

Raw OCR text:
{raw_text}

Cleaned transcription:""",
        description="Prompt for text extraction post-processing",
    )

    ner_extraction: str = Field(
        default="""You are a historical document analyst specializing in named entity recognition.
Extract all named entities from the following transcribed document text.

For each entity, provide:
1. The exact text as it appears
2. The entity type (PERSON, ORGANIZATION, LOCATION, DATE, MONEY, LEGAL_TERM, EVENT, DOCUMENT, OCCUPATION, RELATIONSHIP)
3. A contextual description explaining the entity's role in THIS document
   (e.g., not just "Person" but "Person; the plaintiff filing the complaint")

Document text:
{document_text}

Return entities as a JSON array:
[
  {{
    "text": "John Smith",
    "type": "PERSON", 
    "context": "Person; the plaintiff filing the complaint against the estate"
  }}
]""",
        description="Prompt for NER extraction",
    )

    summary: str = Field(
        default="""You are a historian analyzing a sequence of related documents. The documents 
are provided in chronological order with their dates/timestamps.

Analyze these documents and provide:

## Timeline of Events
A chronological list of key events mentioned or implied across the documents.
Include dates (exact or approximate) and brief descriptions.

## Key Changes
Identify significant changes between documents:
- Shifts in tone, position, or claims
- New information introduced
- Contradictions or amendments to previous statements
- Changes in parties involved

## Research Questions
Suggest 3-5 historical research questions that emerge from these documents:
- Gaps in the record that warrant investigation
- Connections to broader historical contexts
- Potential related sources to consult
- Unanswered questions about motivations or outcomes

Documents:
{documents}""",
        description="Prompt for sequential document summary",
    )


class SummaryConfig(BaseModel):
    """Configuration for Qwen/DashScope summary generation."""

    enabled: bool = Field(default=True, description="Enable summary generation")
    model: str = Field(default="qwen-vl-plus", description="Qwen model to use")
    include_timeline: bool = Field(default=True, description="Include timeline in summary")
    include_key_changes: bool = Field(default=True, description="Include key changes analysis")
    include_research_questions: bool = Field(
        default=True, description="Include research questions"
    )


class OutputConfig(BaseModel):
    """Configuration for output directories."""

    transcriptions_dir: str = Field(default="transcriptions", description="Directory for text files")
    entities_dir: str = Field(default="entities", description="Directory for entity JSON files")
    summaries_dir: str = Field(default="summaries", description="Directory for summary files")
    site_dir: str = Field(default="_site", description="Directory for built static site")


class WebsiteConfig(BaseModel):
    """Configuration for static website."""

    title: str = Field(default="Document Collection", description="Website title")
    emoji: str = Field(default="🐟", description="Emoji displayed next to title")
    background_color: str = Field(default="#1e3a5f", description="Primary background color for header/hero")
    accent_color: str = Field(default="#2563eb", description="Accent color for links and buttons")
    password: str = Field(default="changeme", description="Simple password protection")
    enable_search: bool = Field(default=True, description="Enable Pagefind search")
    enable_browse_dates: bool = Field(default=True, description="Enable browse by dates")
    enable_browse_entities: bool = Field(default=True, description="Enable browse by entities")
    default_sort: str = Field(default="date", description="Default sort order (date, name)")


class FlatfishConfig(BaseModel):
    """Main configuration for Flatfish."""

    dataset: DatasetConfig
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    summary: SummaryConfig = Field(default_factory=SummaryConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    website: WebsiteConfig = Field(default_factory=WebsiteConfig)


class EnvSettings(BaseSettings):
    """Environment variable settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    huggingface_token: str | None = Field(default=None, alias="HUGGINGFACE_TOKEN")
    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")


def load_config(config_path: Path | None = None) -> FlatfishConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to 'flatfish.yaml' in current directory.

    Returns:
        Validated FlatfishConfig instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path("flatfish.yaml")

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            "Run 'flatfish init' to create a new project."
        )

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Config file is empty: {config_path}")

    return FlatfishConfig(**data)


def load_env() -> EnvSettings:
    """Load environment variables from .env file.

    Returns:
        EnvSettings instance with loaded values.
    """
    return EnvSettings()


def get_default_config() -> dict[str, Any]:
    """Get default configuration as a dictionary for generating flatfish.yaml.

    Returns:
        Dictionary with default configuration values.
    """
    return {
        "dataset": {
            "source": "username/dataset-name",
            "splits": ["train"],
            "image_column": "image",
        },
        "processing": {
            "extract_entities": True,
            "entity_context": True,
        },
        "prompts": {
            "text_extraction": PromptsConfig().text_extraction,
            "ner_extraction": PromptsConfig().ner_extraction,
            "summary": PromptsConfig().summary,
        },
        "summary": {
            "enabled": True,
            "model": "qwen-vl-max",
            "include_timeline": True,
            "include_key_changes": True,
            "include_research_questions": True,
        },
        "output": {
            "transcriptions_dir": "transcriptions",
            "entities_dir": "entities",
            "summaries_dir": "summaries",
            "site_dir": "_site",
        },
        "website": {
            "title": "Document Collection",
            "password": "changeme",
            "enable_search": True,
            "enable_browse_dates": True,
            "enable_browse_entities": True,
            "default_sort": "date",
        },
    }
