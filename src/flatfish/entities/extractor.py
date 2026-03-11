"""Entity extraction from transcribed documents using DashScope Qwen API."""

import asyncio
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from openai import AsyncOpenAI

from flatfish.config import FlatfishConfig, EnvSettings
from flatfish.utils.logging import get_logger

logger = get_logger("entities.extractor")

# DashScope international endpoint (OpenAI-compatible)
DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


@dataclass
class Entity:
    """A single extracted entity."""

    text: str
    type: str
    context: str = ""


@dataclass
class EntityExtractionResult:
    """Result of entity extraction from a single document."""

    source_image: str
    entities: list[Entity] = field(default_factory=list)
    model: str = ""
    extracted_at: str = ""


class EntityExtractor:
    """Extracts named entities from transcribed documents using Qwen API."""

    def __init__(
        self,
        config: FlatfishConfig,
        env: EnvSettings,
        base_url: str = DASHSCOPE_BASE_URL,
        timeout: int = 120,
    ):
        """Initialize the entity extractor.

        Args:
            config: Flatfish configuration.
            env: Environment settings with API keys.
            base_url: API base URL.
            timeout: Request timeout in seconds.
        """
        self.config = config
        self.env = env
        self.base_url = base_url
        self.timeout = timeout
        self._async_client: Optional[AsyncOpenAI] = None

    @property
    def async_client(self) -> AsyncOpenAI:
        """Lazy-initialize the async OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.env.dashscope_api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._async_client

    async def extract_entities_async(
        self,
        text: str,
        doc_id: str,
    ) -> EntityExtractionResult:
        """Extract entities from a single document text.

        Args:
            text: The transcribed document text.
            doc_id: Identifier for the source document.

        Returns:
            EntityExtractionResult with extracted entities.
        """
        prompt = self.config.prompts.ner_extraction.format(document_text=text)
        model_name = getattr(self.config.summary, "model", "qwen-vl-plus")

        try:
            response = await self.async_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            raw = response.choices[0].message.content or ""
            entities = self._parse_entities(raw)

            return EntityExtractionResult(
                source_image=doc_id,
                entities=entities,
                model=model_name,
                extracted_at=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"Entity extraction failed for {doc_id}: {e}")
            return EntityExtractionResult(
                source_image=doc_id,
                entities=[],
                model=model_name,
                extracted_at=datetime.now().isoformat(),
            )

    def _parse_entities(self, raw_text: str) -> list[Entity]:
        """Parse entity JSON from LLM response.

        Args:
            raw_text: Raw LLM response text.

        Returns:
            List of parsed Entity objects.
        """
        # Try to extract JSON array from the response
        json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
        if not json_match:
            logger.warning("No JSON array found in entity response")
            return []

        try:
            items = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse entity JSON: {e}")
            return []

        entities = []
        for item in items:
            if isinstance(item, dict) and "text" in item and "type" in item:
                entities.append(
                    Entity(
                        text=item["text"],
                        type=item.get("type", "UNKNOWN"),
                        context=item.get("context", ""),
                    )
                )
        return entities

    async def extract_batch_async(
        self,
        documents: list[dict],
        max_concurrent: int = 10,
        on_complete: Optional[Callable] = None,
    ) -> list[EntityExtractionResult]:
        """Extract entities from multiple documents concurrently.

        Args:
            documents: List of dicts with 'id' and 'text' keys.
            max_concurrent: Maximum concurrent API requests.
            on_complete: Optional callback called with each result as it completes.

        Returns:
            List of EntityExtractionResult objects.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def process_one(doc: dict) -> EntityExtractionResult:
            async with semaphore:
                result = await self.extract_entities_async(
                    text=doc["text"],
                    doc_id=doc["id"],
                )
                if on_complete:
                    on_complete(result)
                return result

        tasks = [process_one(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Entity extraction task failed: {r}")
            else:
                valid_results.append(r)

        return valid_results

    def save_entities(
        self,
        result: EntityExtractionResult,
        output_dir: Path,
    ) -> Path:
        """Save entity extraction result to a JSON file.

        Args:
            result: The extraction result to save.
            output_dir: Directory to save the file in.

        Returns:
            Path to the saved file.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{result.source_image}.json"
        data = {
            "source_image": result.source_image,
            "entities": [asdict(e) for e in result.entities],
            "model": result.model,
            "extracted_at": result.extracted_at,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path


def load_entities(entity_file: Path) -> EntityExtractionResult:
    """Load entity extraction result from a JSON file.

    Args:
        entity_file: Path to the JSON file.

    Returns:
        EntityExtractionResult loaded from disk.
    """
    with open(entity_file, encoding="utf-8") as f:
        data = json.load(f)

    entities = [
        Entity(
            text=e["text"],
            type=e["type"],
            context=e.get("context", ""),
        )
        for e in data.get("entities", [])
    ]

    return EntityExtractionResult(
        source_image=data.get("source_image", entity_file.stem),
        entities=entities,
        model=data.get("model", ""),
        extracted_at=data.get("extracted_at", ""),
    )


def consolidate_entities(
    results: list[EntityExtractionResult],
) -> dict:
    """Consolidate entities from multiple documents into a summary.

    Groups entities by type and deduplicates.

    Args:
        results: List of EntityExtractionResult from individual documents.

    Returns:
        Dict with 'by_type' and 'all_entities' keys.
    """
    by_type: dict[str, dict[str, dict]] = defaultdict(dict)
    all_entities: list[dict] = []

    for result in results:
        for entity in result.entities:
            key = f"{entity.text}|{entity.type}"

            if key not in by_type.get(entity.type, {}):
                entry = {
                    "text": entity.text,
                    "type": entity.type,
                    "context": entity.context,
                    "sources": [result.source_image],
                    "count": 1,
                }
                by_type[entity.type][key] = entry
                all_entities.append(entry)
            else:
                existing = by_type[entity.type][key]
                if result.source_image not in existing["sources"]:
                    existing["sources"].append(result.source_image)
                existing["count"] += 1

    # Convert by_type to serializable format
    by_type_out = {}
    for entity_type, entities_map in by_type.items():
        by_type_out[entity_type] = sorted(
            entities_map.values(),
            key=lambda e: e["count"],
            reverse=True,
        )

    return {
        "by_type": by_type_out,
        "all_entities": sorted(all_entities, key=lambda e: e["count"], reverse=True),
    }
