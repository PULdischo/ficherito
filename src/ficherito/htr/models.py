"""HTR model using OpenAI-compatible API for DashScope Qwen-VL."""

import asyncio
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, Union, Callable

from openai import OpenAI, AsyncOpenAI

from ficherito.utils.logging import get_logger

logger = get_logger("htr.models")

# DashScope international endpoint (OpenAI-compatible)
DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# Default VLM models for different use cases
DEFAULT_MODELS = {
    "default": "qwen-vl-max",
    "fast": "qwen-vl-plus",
    "best": "qwen-vl-max",
}


class HTRModel:
    """Wrapper for DashScope Qwen-VL models using OpenAI-compatible API."""

    def __init__(
        self,
        model_name: str = "qwen-vl-max",
        api_key: Optional[str] = None,
        base_url: str = DASHSCOPE_BASE_URL,
        timeout: int = 360,
    ):
        """Initialize the HTR model.

        Args:
            model_name: Qwen-VL model to use.
            api_key: DashScope API key.
            base_url: API base URL.
            timeout: Request timeout in seconds.
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None

    @property
    def sync_client(self) -> OpenAI:
        """Lazy-initialize the sync OpenAI client."""
        if self._sync_client is None:
            self._sync_client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._sync_client

    @property
    def async_client(self) -> AsyncOpenAI:
        """Lazy-initialize the async OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._async_client

    def extract_text(
        self,
        image_base64: str,
        prompt: str,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, Optional[float]]:
        """Extract text from an image using Qwen-VL (sync).

        Args:
            image_base64: Base64-encoded image data.
            prompt: Prompt for text extraction.
            max_tokens: Maximum tokens to generate. Many providers default to
                a low limit when this isn't set, silently truncating longer
                (e.g. multi-page) transcriptions.

        Returns:
            Tuple of (extracted_text, confidence).
        """
        # Ensure proper data URL format
        if not image_base64.startswith("data:"):
            image_url = f"data:image/jpeg;base64,{image_base64}"
        else:
            image_url = image_base64

        try:
            completion = self.sync_client.chat.completions.create(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ]
                }],
                max_tokens=max_tokens,
            )

            if completion.choices[0].finish_reason == "length":
                logger.warning(
                    f"HTR response truncated at max_tokens={max_tokens}; "
                    "increase processing.max_output_tokens in ficherito.yaml"
                )

            text = completion.choices[0].message.content or ""
            return text.strip(), None

        except Exception as e:
            logger.error(f"HTR extraction failed: {e}")
            return "", None

    async def extract_text_async(
        self,
        image_base64: str,
        prompt: str,
        max_tokens: Optional[int] = None,
    ) -> tuple[str, Optional[float]]:
        """Extract text from an image using Qwen-VL (async).

        Args:
            image_base64: Base64-encoded image data.
            prompt: Prompt for text extraction.
            max_tokens: Maximum tokens to generate. Many providers default to
                a low limit when this isn't set, silently truncating longer
                (e.g. multi-page) transcriptions.

        Returns:
            Tuple of (extracted_text, confidence).
        """
        # Ensure proper data URL format
        if not image_base64.startswith("data:"):
            image_url = f"data:image/jpeg;base64,{image_base64}"
        else:
            image_url = image_base64

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ]
                    }],
                    max_tokens=max_tokens,
                ),
                timeout=self.timeout
            )

            if completion.choices[0].finish_reason == "length":
                logger.warning(
                    f"HTR response truncated at max_tokens={max_tokens}; "
                    "increase processing.max_output_tokens in ficherito.yaml"
                )

            text = completion.choices[0].message.content or ""
            return text.strip(), None

        except asyncio.TimeoutError:
            logger.error(f"HTR extraction timed out after {self.timeout}s")
            return "", None
        except Exception as e:
            logger.error(f"HTR extraction failed: {e}")
            return "", None

    async def transcribe_single(
        self,
        image_id: str,
        image_base64: str,
        prompt: str,
        semaphore: asyncio.Semaphore,
    ) -> Optional[dict]:
        """Process a single image with rate limiting."""
        async with semaphore:
            text, confidence = await self.extract_text_async(image_base64, prompt)
            if text:
                return {"id": image_id, "text": text, "confidence": confidence}
            return None

    async def transcribe_batch_streaming(
        self,
        images: list[tuple[str, str]],
        prompt: str,
        max_concurrent: int = 15,
        on_complete: Optional[Callable[[dict], None]] = None,
    ) -> list[dict]:
        """Process all images with concurrency control, streaming results as they complete.

        Args:
            images: List of (image_id, image_base64) tuples.
            prompt: Prompt for text extraction.
            max_concurrent: Maximum concurrent requests.
            on_complete: Optional callback called when each result completes.

        Returns:
            List of dicts with 'id', 'text', and 'confidence' keys.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # Create tasks
        tasks = [
            asyncio.create_task(self.transcribe_single(img_id, img_b64, prompt, semaphore))
            for img_id, img_b64 in images
        ]
        
        results = []
        
        # Process results as they complete (like tqdm.as_completed)
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                if result:
                    results.append(result)
                    if on_complete:
                        on_complete(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")
        
        return results

    async def extract_batch_async(
        self,
        images: list[tuple[str, str]],
        prompt: str,
        max_concurrent: int = 15,
    ) -> list[dict]:
        """Extract text from multiple images concurrently.

        Args:
            images: List of (image_id, image_base64) tuples.
            prompt: Prompt for text extraction.
            max_concurrent: Maximum concurrent requests.

        Returns:
            List of dicts with 'id' and 'text' keys.
        """
        return await self.transcribe_batch_streaming(images, prompt, max_concurrent)

    async def _extract_single(
        self,
        image_id: str,
        image_base64: str,
        prompt: str,
        semaphore: asyncio.Semaphore,
    ) -> Optional[dict]:
        """Process a single image with rate limiting."""
        async with semaphore:
            text, _ = await self.extract_text_async(image_base64, prompt)
            if text:
                return {"id": image_id, "text": text}
            return None


def get_model(
    model_type: str = "default",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> HTRModel:
    """Get an HTR model instance.

    Args:
        model_type: Type of model ('default', 'fast', 'best').
        model_name: Specific model name (overrides model_type).
        api_key: Optional API key.
        base_url: Optional API base URL (overrides the built-in default).

    Returns:
        HTRModel instance.
    """
    if model_name is None:
        model_name = DEFAULT_MODELS.get(model_type, DEFAULT_MODELS["default"])

    kwargs = {"model_name": model_name, "api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return HTRModel(**kwargs)


def image_to_base64(image: Union["Image.Image", Path, str, bytes]) -> str:
    """Convert various image formats to base64 string.

    Args:
        image: PIL Image, file path, or bytes.

    Returns:
        Base64-encoded string.
    """
    from PIL import Image

    if isinstance(image, bytes):
        return base64.b64encode(image).decode("utf-8")

    if isinstance(image, (str, Path)):
        with open(image, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    # PIL Image
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")
