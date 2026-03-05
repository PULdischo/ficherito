"""Translation module for Flatfish."""

from flatfish.translation.translator import (
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
