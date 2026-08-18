"""Configuration loading and validation for Ficherito."""

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatasetConfig(BaseModel):
    """Configuration for the local folder of document images."""

    images_dir: str = Field(default="images", description="Local folder containing document images")
    recursive: bool = Field(default=False, description="Search subfolders recursively for images")


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

class TranslateConfig(BaseModel):
    """Configuration for document translation."""

    enabled: bool = Field(default=False, description="Enable translation")
    source_languages: list[str] = Field(
        default=["es"], 
        description="Source language codes (e.g., 'es', 'fr', 'de')"
    )
    target_language: str = Field(
        default="en", 
        description="Target language code for translation"
    )
    default_tab: str = Field(
        default="transcription",
        description="Which tab to show by default: 'transcription' or 'translation'"
    )


class OutputConfig(BaseModel):
    """Configuration for output directories."""

    transcriptions_dir: str = Field(default="transcriptions", description="Directory for text files")
    translations_dir: str = Field(default="translations", description="Directory for translation files")
    entities_dir: str = Field(default="entities", description="Directory for entity JSON files")
    eleventy_dir: str = Field(default="site", description="Directory for the Eleventy (11ty) site project")
    site_dir: str = Field(default="site/_site", description="Directory for the built static site (Eleventy output)")


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
    netlify_site_id: Optional[str] = Field(default=None, description="Netlify site ID for deployment")


class FicheritoConfig(BaseModel):
    """Main configuration for Ficherito."""

    dataset: DatasetConfig
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    translate: TranslateConfig = Field(default_factory=TranslateConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    website: WebsiteConfig = Field(default_factory=WebsiteConfig)


class EnvSettings(BaseSettings):
    """Environment variable settings.

    The LLM endpoint is OpenAI-compatible and fully configurable via .env so
    any provider (DashScope, OpenAI, local, etc.) can be used.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    api_model: str | None = Field(default=None, alias="OPENAI_MODEL")


def load_config(config_path: Path | None = None) -> FicheritoConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to 'ficherito.yaml' in current directory.

    Returns:
        Validated FicheritoConfig instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path("ficherito.yaml")

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            "Run 'ficherito init' to create a new project."
        )

    with open(config_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Config file is empty: {config_path}")

    return FicheritoConfig(**data)


def load_env() -> EnvSettings:
    """Load environment variables from .env file.

    Returns:
        EnvSettings instance with loaded values.
    """
    return EnvSettings()


def get_default_config() -> dict[str, Any]:
    """Get default configuration as a dictionary for generating ficherito.yaml.

    Returns:
        Dictionary with default configuration values.
    """
    return {
        "dataset": {
            "images_dir": "images",
            "recursive": False,
        },
        "processing": {
            "extract_entities": True,
            "entity_context": True,
        },
        "prompts": {
            "text_extraction": PromptsConfig().text_extraction,
            "ner_extraction": PromptsConfig().ner_extraction,
        },
        "translate": {
            "enabled": False,
            "source_languages": ["es"],
            "target_language": "en",
            "default_tab": "transcription",
        },
        "output": {
            "transcriptions_dir": "transcriptions",
            "translations_dir": "translations",
            "entities_dir": "entities",
            "eleventy_dir": "site",
            "site_dir": "site/_site",
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
