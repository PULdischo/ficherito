"""Translation engine using deep_translator."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException

from ficherito.config import FicheritoConfig
from ficherito.utils.logging import get_logger

logger = get_logger("translation")

# Valid language codes for GoogleTranslator
SUPPORTED_LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)


def get_supported_languages() -> dict[str, str]:
    """Get dictionary of supported language codes and names.
    
    Returns:
        Dictionary mapping language codes to language names.
    """
    return SUPPORTED_LANGUAGES


def validate_languages(source_languages: list[str], target_language: str) -> tuple[bool, str]:
    """Validate that all languages are supported by GoogleTranslator.
    
    Args:
        source_languages: List of source language codes.
        target_language: Target language code.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    supported = get_supported_languages()
    
    # Validate target language
    if target_language not in supported and target_language not in supported.values():
        return False, f"Target language '{target_language}' is not supported. Supported languages: {list(supported.keys())[:20]}..."
    
    # Validate source languages
    invalid_sources = []
    for lang in source_languages:
        if lang not in supported and lang not in supported.values():
            invalid_sources.append(lang)
    
    if invalid_sources:
        return False, f"Source language(s) {invalid_sources} not supported. Supported languages: {list(supported.keys())[:20]}..."
    
    return True, ""


@dataclass
class TranslationResult:
    """Result of a single document translation."""
    
    document_id: str
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    success: bool = True
    error: Optional[str] = None


class Translator:
    """Translates documents using GoogleTranslator from deep_translator."""
    
    def __init__(
        self,
        config: FicheritoConfig,
    ):
        """Initialize the translator.
        
        Args:
            config: Ficherito configuration.
        """
        self.config = config
        self.source_languages = config.translate.source_languages
        self.target_language = config.translate.target_language
        
        # Validate languages on init
        is_valid, error = validate_languages(self.source_languages, self.target_language)
        if not is_valid:
            raise ValueError(error)
    
    def translate_text(self, text: str, source_language: str = "auto") -> str:
        """Translate a single text.
        
        Args:
            text: Text to translate.
            source_language: Source language code or "auto" for detection.
            
        Returns:
            Translated text.
        """
        if not text.strip():
            return ""
        
        translator = GoogleTranslator(source=source_language, target=self.target_language)
        
        # GoogleTranslator has a 5000 character limit, so we need to chunk
        max_chars = 4500
        
        if len(text) <= max_chars:
            return translator.translate(text)
        
        # Split by paragraphs and translate in chunks
        paragraphs = text.split('\n\n')
        translated_parts = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += para + "\n\n"
            else:
                # Translate current chunk
                if current_chunk.strip():
                    translated_parts.append(translator.translate(current_chunk.strip()))
                current_chunk = para + "\n\n"
        
        # Translate remaining chunk
        if current_chunk.strip():
            translated_parts.append(translator.translate(current_chunk.strip()))
        
        return "\n\n".join(translated_parts)
    
    def translate_document(
        self,
        doc_id: str,
        text: str,
        source_language: str = "auto",
    ) -> TranslationResult:
        """Translate a single document.
        
        Args:
            doc_id: Document identifier.
            text: Text to translate.
            source_language: Source language code or "auto".
            
        Returns:
            TranslationResult with translated text.
        """
        try:
            translated = self.translate_text(text, source_language)
            return TranslationResult(
                document_id=doc_id,
                source_language=source_language,
                target_language=self.target_language,
                original_text=text,
                translated_text=translated,
                success=True,
            )
        except Exception as e:
            logger.error(f"Translation failed for {doc_id}: {e}")
            return TranslationResult(
                document_id=doc_id,
                source_language=source_language,
                target_language=self.target_language,
                original_text=text,
                translated_text="",
                success=False,
                error=str(e),
            )
    
    def save_translation(
        self,
        result: TranslationResult,
        output_dir: Path,
    ) -> Path:
        """Save a translation result to a markdown file.
        
        Args:
            result: TranslationResult to save.
            output_dir: Directory to save translation files.
            
        Returns:
            Path to the saved file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{result.document_id}.md"
        
        # Write as markdown with metadata header
        content = f"""---
source_language: {result.source_language}
target_language: {result.target_language}
---

{result.translated_text}
"""
        
        output_file.write_text(content, encoding="utf-8")
        logger.debug(f"Saved translation: {output_file}")
        return output_file


def load_translation(file_path: Path) -> tuple[str, dict]:
    """Load a translation from a markdown file.
    
    Args:
        file_path: Path to the translation file.
        
    Returns:
        Tuple of (translation_text, metadata_dict).
    """
    content = file_path.read_text(encoding="utf-8")
    
    metadata = {}
    text = content
    
    # Parse YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
            text = parts[2].strip()
    
    return text, metadata
