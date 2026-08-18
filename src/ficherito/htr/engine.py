"""HTR engine for text extraction from images using DashScope Qwen-VL."""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from PIL import Image

from ficherito.config import FicheritoConfig, EnvSettings
from ficherito.htr.models import HTRModel, get_model, image_to_base64
from ficherito.utils.images import prepare_for_ocr
from ficherito.utils.logging import get_logger
from ficherito.utils.text import clean_extracted_text

logger = get_logger("htr.engine")


# Default prompt for HTR extraction
DEFAULT_HTR_PROMPT = """You are a historical document transcription expert. 
Carefully examine this handwritten document image and transcribe all visible text exactly as written.

Instructions:
1. Preserve original spelling, including archaic forms
2. Maintain line breaks where they appear meaningful
3. Mark unclear or illegible text with [?] or [illegible]
4. Include any visible dates, names, or numbers
5. Do not add interpretation or commentary - only transcribe what you see

Transcribe the document:"""


@dataclass
class TranscriptionResult:
    """Result of text extraction from an image."""

    image_id: str
    text: str
    confidence: Optional[float] = None
    model_name: str = ""
    extracted_at: str = ""


class HTREngine:
    """Engine for extracting text from document images using DashScope."""

    def __init__(
        self,
        config: FicheritoConfig,
        env: Optional[EnvSettings] = None,
        model: Optional[HTRModel] = None,
    ):
        """Initialize the HTR engine.

        Args:
            config: Ficherito configuration.
            env: Environment settings with API key.
            model: Optional pre-loaded model.
        """
        self.config = config
        self.env = env
        self._model = model

    @property
    def model(self) -> HTRModel:
        """Get or load the HTR model."""
        if self._model is None:
            api_key = self.env.api_key if self.env else None
            base_url = self.env.api_base_url if self.env else None
            model_name = self.env.api_model if self.env else None
            self._model = get_model(api_key=api_key, base_url=base_url, model_name=model_name)
        return self._model

    def extract_text(
        self,
        image: Image.Image,
        image_id: str,
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """Extract text from a single image.

        Args:
            image: PIL Image to process.
            image_id: Identifier for the image.
            prompt: Optional custom prompt (uses config prompt or default).

        Returns:
            TranscriptionResult with extracted text.
        """
        # Prepare image
        img = prepare_for_ocr(image, max_size=(2048, 2048))

        # Convert to base64
        img_base64 = image_to_base64(img)

        # Get prompt
        if prompt is None:
            # Use prompt from config, or fall back to default
            prompt = getattr(self.config.prompts, 'text_extraction', None)
            if not prompt or '{raw_text}' in prompt:
                # The config prompt is for post-processing, use HTR-specific prompt
                prompt = DEFAULT_HTR_PROMPT

        # Extract text via DashScope
        text, confidence = self.model.extract_text(img_base64, prompt)

        # Clean extracted text
        cleaned_text = clean_extracted_text(text)

        return TranscriptionResult(
            image_id=image_id,
            text=cleaned_text,
            confidence=confidence,
            model_name=self.model.model_name,
            extracted_at=datetime.utcnow().isoformat() + "Z",
        )

    def extract_batch(
        self,
        images: list[tuple[Image.Image, str]],
    ) -> list[TranscriptionResult]:
        """Extract text from multiple images.

        Note: DashScope processes one image at a time, so this iterates sequentially.

        Args:
            images: List of (image, image_id) tuples.

        Returns:
            List of TranscriptionResult objects.
        """
        results = []

        for img, image_id in images:
            result = self.extract_text(img, image_id)
            results.append(result)

        return results

    async def extract_text_async(
        self,
        image: Image.Image,
        image_id: str,
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """Extract text from a single image asynchronously.

        Args:
            image: PIL Image to process.
            image_id: Identifier for the image.
            prompt: Optional custom prompt.

        Returns:
            TranscriptionResult with extracted text.
        """
        # Prepare image
        img = prepare_for_ocr(image, max_size=(2048, 2048))
        img_base64 = image_to_base64(img)

        # Get prompt
        if prompt is None:
            prompt = getattr(self.config.prompts, 'text_extraction', None)
            if not prompt or '{raw_text}' in prompt:
                prompt = DEFAULT_HTR_PROMPT

        # Extract text via async API
        text, confidence = await self.model.extract_text_async(img_base64, prompt)

        # Clean extracted text
        cleaned_text = clean_extracted_text(text)

        return TranscriptionResult(
            image_id=image_id,
            text=cleaned_text,
            confidence=confidence,
            model_name=self.model.model_name,
            extracted_at=datetime.utcnow().isoformat() + "Z",
        )

    async def extract_batch_async(
        self,
        images: list[tuple[Image.Image, str]],
        max_concurrent: int = 15,
        on_complete: Optional[Callable[[TranscriptionResult], None]] = None,
    ) -> list[TranscriptionResult]:
        """Extract text from multiple images concurrently, streaming results.

        Uses asyncio.as_completed to process results as they finish,
        similar to tqdm.as_completed for better performance.

        Args:
            images: List of (image, image_id) tuples.
            max_concurrent: Maximum concurrent API requests.
            on_complete: Optional callback called when each extraction completes.

        Returns:
            List of TranscriptionResult objects.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_single(img: Image.Image, image_id: str) -> TranscriptionResult:
            async with semaphore:
                return await self.extract_text_async(img, image_id)

        # Create all tasks
        tasks = [
            asyncio.create_task(extract_single(img, image_id))
            for img, image_id in images
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
                logger.error(f"Failed to extract text: {e}")

        return results

    def save_transcription(
        self,
        result: TranscriptionResult,
        output_dir: Path,
    ) -> Path:
        """Save transcription to a Markdown file with YAML frontmatter.

        Args:
            result: TranscriptionResult to save.
            output_dir: Directory to save to.

        Returns:
            Path to saved file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{result.image_id}.md"

        # Build YAML frontmatter
        frontmatter = {
            "title": result.image_id,
            "extracted_at": result.extracted_at,
            "model": result.model_name,
        }
        if result.confidence is not None:
            frontmatter["confidence"] = round(result.confidence, 2)

        # Format as Markdown with YAML frontmatter
        import yaml
        yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        
        content = f"""---
{yaml_str.strip()}
---

{result.text}
"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Saved transcription: {output_path}")
        return output_path


def load_transcription(file_path: Path) -> tuple[str, dict]:
    """Load a transcription from a Markdown file with YAML frontmatter.

    Args:
        file_path: Path to transcription file (.md or .txt).

    Returns:
        Tuple of (text, metadata dict).
    """
    import yaml
    
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    metadata = {}
    text = content

    # Check for YAML frontmatter (starts with ---)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            # parts[0] is empty, parts[1] is YAML, parts[2] is content
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                metadata = {}
            text = parts[2].strip()
    else:
        # Legacy format: [Key: Value] headers
        lines = content.split("\n")
        text_start = 0
        for i, line in enumerate(lines):
            if line.startswith("[") and line.endswith("]"):
                inner = line[1:-1]
                if ": " in inner:
                    key, value = inner.split(": ", 1)
                    metadata[key.lower()] = value
            elif line.strip() == "---":
                text_start = i + 1
                break
        text = "\n".join(lines[text_start:]).strip()

    return text, metadata
