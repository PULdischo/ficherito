"""Translation module for Ficherito."""

from ficherito.translation.translator import (
    Translator,
    TranslationResult,
    validate_languages,
    get_supported_languages,
)

__all__ = [
    "Translator",
    "TranslationResult",
    "validate_languages",
    "get_supported_languages",
]
