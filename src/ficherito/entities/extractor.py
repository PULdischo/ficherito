"""Entity extraction from transcribed text."""

import asyncio
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from openai import OpenAI, AsyncOpenAI

from ficherito.config import FicheritoConfig, EnvSettings
from ficherito.utils.logging import get_logger
from ficherito.utils.text import extract_json_from_response, clean_extracted_text

logger = get_logger("entities.extractor")

# DashScope international endpoint (OpenAI-compatible)
DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


@dataclass
class Entity:
    """Represents an extracted entity."""

    text: str
    type: str
    context: str
    positions: list[dict] = field(default_factory=list)
    confidence: Optional[float] = None


@dataclass
class EntityExtractionResult:
    """Result of entity extraction from a document."""

    source_image: str
    extracted_at: str
    entities: list[Entity]


class EntityExtractor:
    """Extracts named entities from transcribed text using LLM."""

    def __init__(
        self,
        config: FicheritoConfig,
        env: EnvSettings,
        base_url: str = DASHSCOPE_BASE_URL,
        timeout: int = 120,
    ):
        """Initialize the entity extractor.

        Args:
            config: Ficherito configuration.
            env: Environment settings with API keys.
            base_url: Fallback API base URL if not set in the environment.
            timeout: Request timeout in seconds.
        """
        self.config = config
        self.env = env
        self.base_url = env.api_base_url or base_url
        self.model = env.api_model or "qwen-turbo"
        self.timeout = timeout
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None

    @property
    def sync_client(self) -> OpenAI:
        """Lazy-initialize the sync OpenAI client."""
        if self._sync_client is None:
            self._sync_client = OpenAI(
                api_key=self.env.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._sync_client

    @property
    def async_client(self) -> AsyncOpenAI:
        """Lazy-initialize the async OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.env.api_key,
                base_url=self.base_url,
            )
        return self._async_client

    def extract_entities(
        self,
        text: str,
        image_id: str,
        model: Optional[str] = None,
    ) -> EntityExtractionResult:
        """Extract entities from text (sync).

        Args:
            text: Transcribed document text.
            image_id: Identifier for the source image.
            model: Model to use for extraction.

        Returns:
            EntityExtractionResult with extracted entities.
        """
        model = model or self.model
        # Clean input text before extraction
        cleaned_text = clean_extracted_text(text)
        
        # Build prompt
        prompt = self.config.prompts.ner_extraction.format(document_text=cleaned_text)

        try:
            completion = self.sync_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.processing.max_output_tokens,
            )

            if completion.choices[0].finish_reason == "length":
                logger.warning(
                    f"Entity extraction response truncated at "
                    f"max_tokens={self.config.processing.max_output_tokens} for {image_id}; "
                    "increase processing.max_output_tokens in ficherito.yaml"
                )

            content = completion.choices[0].message.content or ""
            logger.debug(f"Entity extraction response: {content[:500]}...")
            entities = self._parse_entities(content, cleaned_text)

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            logger.debug(f"Raw response content was: {content if 'content' in dir() else 'N/A'}")
            entities = []

        return EntityExtractionResult(
            source_image=image_id,
            extracted_at=datetime.utcnow().isoformat() + "Z",
            entities=entities,
        )

    async def extract_entities_async(
        self,
        text: str,
        image_id: str,
        model: Optional[str] = None,
    ) -> EntityExtractionResult:
        """Extract entities from text (async).

        Args:
            text: Transcribed document text.
            image_id: Identifier for the source image.
            model: Model to use for extraction.

        Returns:
            EntityExtractionResult with extracted entities.
        """
        model = model or self.model
        # Clean input text before extraction
        cleaned_text = clean_extracted_text(text)
        
        # Build prompt
        prompt = self.config.prompts.ner_extraction.format(document_text=cleaned_text)

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config.processing.max_output_tokens,
                ),
                timeout=self.timeout
            )

            if completion.choices[0].finish_reason == "length":
                logger.warning(
                    f"Entity extraction response truncated at "
                    f"max_tokens={self.config.processing.max_output_tokens} for {image_id}; "
                    "increase processing.max_output_tokens in ficherito.yaml"
                )

            content = completion.choices[0].message.content or ""
            entities = self._parse_entities(content, cleaned_text)

        except asyncio.TimeoutError:
            logger.error(f"Entity extraction timed out after {self.timeout}s")
            entities = []
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            entities = []

        return EntityExtractionResult(
            source_image=image_id,
            extracted_at=datetime.utcnow().isoformat() + "Z",
            entities=entities,
        )

    async def extract_batch_async(
        self,
        documents: list[dict],
        model: Optional[str] = None,
        max_concurrent: int = 15,
        on_complete: Optional[Callable[["EntityExtractionResult"], None]] = None,
    ) -> list[EntityExtractionResult]:
        """Extract entities from multiple documents concurrently, streaming results.

        Uses asyncio.as_completed to process results as they finish.

        Args:
            documents: List of dicts with 'id' and 'text' keys.
            model: Model to use for extraction.
            max_concurrent: Maximum concurrent requests.
            on_complete: Optional callback called when each extraction completes.

        Returns:
            List of EntityExtractionResult objects.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_single(doc: dict) -> EntityExtractionResult:
            async with semaphore:
                return await self.extract_entities_async(
                    text=doc["text"],
                    image_id=doc["id"],
                    model=model,
                )

        # Create all tasks
        tasks = [
            asyncio.create_task(extract_single(doc))
            for doc in documents
        ]
        
        # Process results as they complete (streaming)
        results = []
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
                if on_complete:
                    on_complete(result)
            except Exception as e:
                logger.error(f"Failed to extract entities: {e}")
        
        return results

    def _parse_entities(self, response: str, source_text: str) -> list[Entity]:
        """Parse entities from LLM response.

        Args:
            response: LLM response text.
            source_text: Original document text.

        Returns:
            List of Entity objects.
        """
        entities = []

        # Extract JSON from response (handles code fences)
        json_str = extract_json_from_response(response)
        if not json_str:
            logger.warning("No JSON found in response")
            return entities

        try:
            data = json.loads(json_str)
            
            # Handle both array and object responses
            if isinstance(data, dict):
                # If it's an object, look for an 'entities' key or convert to list
                data = data.get('entities', [data])

            for item in data:
                if not isinstance(item, dict):
                    continue

                text = item.get("text", "")
                entity_type = item.get("type", "UNKNOWN")
                context = item.get("context", "")

                if not text:
                    continue

                # Find positions in source text
                positions = []
                start = 0
                while True:
                    pos = source_text.find(text, start)
                    if pos == -1:
                        break
                    positions.append({"start": pos, "end": pos + len(text)})
                    start = pos + 1

                entities.append(
                    Entity(
                        text=text,
                        type=entity_type,
                        context=context,
                        positions=positions,
                        confidence=item.get("confidence"),
                    )
                )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")

        return entities

    def save_entities(
        self,
        result: EntityExtractionResult,
        output_dir: Path,
    ) -> Path:
        """Save entities to a JSON file.

        Args:
            result: EntityExtractionResult to save.
            output_dir: Directory to save to.

        Returns:
            Path to saved file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{result.source_image}.json"

        # Convert to dict
        data = {
            "source_image": result.source_image,
            "extracted_at": result.extracted_at,
            "entities": [asdict(e) for e in result.entities],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved entities: {output_path}")
        return output_path


def load_entities(file_path: Path) -> EntityExtractionResult:
    """Load entities from a JSON file.

    Args:
        file_path: Path to entities file.

    Returns:
        EntityExtractionResult object.
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    entities = [
        Entity(
            text=e["text"],
            type=e["type"],
            context=e["context"],
            positions=e.get("positions", []),
            confidence=e.get("confidence"),
        )
        for e in data.get("entities", [])
    ]

    return EntityExtractionResult(
        source_image=data["source_image"],
        extracted_at=data["extracted_at"],
        entities=entities,
    )


def consolidate_entities(results: list[EntityExtractionResult]) -> dict:
    """Consolidate entities from multiple documents.

    Groups entities by type and text, tracking which documents they appear in.

    Args:
        results: List of EntityExtractionResult objects.

    Returns:
        Dictionary with consolidated entity data.
    """
    # Group by entity text and type
    entity_map: dict[tuple[str, str], dict] = {}

    for result in results:
        for entity in result.entities:
            key = (entity.text, entity.type)

            if key not in entity_map:
                entity_map[key] = {
                    "text": entity.text,
                    "type": entity.type,
                    "contexts": [],
                    "documents": [],
                    "count": 0,
                }

            entity_map[key]["contexts"].append({
                "document": result.source_image,
                "context": entity.context,
            })
            entity_map[key]["documents"].append(result.source_image)
            entity_map[key]["count"] += 1

    # Convert to list and sort by count
    entities = sorted(entity_map.values(), key=lambda x: x["count"], reverse=True)

    # Group by type
    by_type: dict[str, list] = {}
    for entity in entities:
        entity_type = entity["type"]
        if entity_type not in by_type:
            by_type[entity_type] = []
        by_type[entity_type].append(entity)

    return {
        "total_entities": len(entities),
        "unique_texts": len(entity_map),
        "by_type": by_type,
        "all_entities": entities,
    }
