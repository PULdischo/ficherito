"""Entity extraction from transcribed documents."""

from flatfish.entities.extractor import (
    EntityExtractor,
    EntityExtractionResult,
    Entity,
    consolidate_entities,
    load_entities,
)

__all__ = [
    "EntityExtractor",
    "EntityExtractionResult",
    "Entity",
    "consolidate_entities",
    "load_entities",
]
