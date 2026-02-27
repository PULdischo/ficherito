"""Qwen/DashScope integration for document summary generation."""

import asyncio
import base64
import json
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from openai import OpenAI, AsyncOpenAI
from PIL import Image

from flatfish.config import FlatfishConfig, EnvSettings
from flatfish.utils.dates import sort_by_date
from flatfish.utils.logging import get_logger

logger = get_logger("summary.qwen")

# DashScope international endpoint (OpenAI-compatible)
DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


def image_to_base64(image: Union[Image.Image, Path, str, bytes]) -> str:
    """Convert various image formats to base64 string.

    Args:
        image: PIL Image, file path, or bytes.

    Returns:
        Base64-encoded image string.
    """
    if isinstance(image, bytes):
        return base64.b64encode(image).decode("utf-8")

    if isinstance(image, (str, Path)):
        with open(image, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    if isinstance(image, Image.Image):
        buffer = BytesIO()
        # Convert to RGB if necessary
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("utf-8")

    raise ValueError(f"Unsupported image type: {type(image)}")


@dataclass
class DocumentSummary:
    """Summary generated from a sequence of documents."""

    timeline: list[dict]
    key_changes: list[dict]
    research_questions: list[str]
    full_text: str
    generated_at: str
    model: str
    document_count: int


class QwenSummarizer:
    """Generates summaries from document sequences using Qwen-VL multimodal API."""

    # Maximum images per API call (Qwen-VL limit)
    MAX_IMAGES_PER_CALL = 20

    def __init__(
        self,
        config: FlatfishConfig,
        env: EnvSettings,
        base_url: str = DASHSCOPE_BASE_URL,
        timeout: int = 360,
    ):
        """Initialize the summarizer.

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
        self._sync_client: Optional[OpenAI] = None
        self._async_client: Optional[AsyncOpenAI] = None

    @property
    def sync_client(self) -> OpenAI:
        """Lazy-initialize the sync OpenAI client."""
        if self._sync_client is None:
            self._sync_client = OpenAI(
                api_key=self.env.dashscope_api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._sync_client

    @property
    def async_client(self) -> AsyncOpenAI:
        """Lazy-initialize the async OpenAI client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.env.dashscope_api_key,
                base_url=self.base_url,
            )
        return self._async_client

    def generate_summary(
        self,
        documents: list[dict],
        model: Optional[str] = None,
    ) -> DocumentSummary:
        """Generate a summary from a sequence of documents with images (sync).

        Args:
            documents: List of document dicts with 'id', 'date', 'image', and optionally 'text' keys.
            model: Model to use (defaults to config value).

        Returns:
            DocumentSummary object.
        """
        model = model or self.config.summary.model

        # Sort documents by date
        sorted_docs = sort_by_date(documents, date_key="date")

        # Process in batches if needed
        if len(sorted_docs) > self.MAX_IMAGES_PER_CALL:
            # For large batches, use async
            return asyncio.run(self._generate_batched_summary_async(sorted_docs, model))

        # Build multimodal message with images and timestamps
        content = self._build_multimodal_content(sorted_docs)

        # Add the summary prompt at the end
        prompt = self.config.prompts.summary
        content.append({"type": "text", "text": prompt})

        try:
            completion = self.sync_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
            )

            result_text = completion.choices[0].message.content or ""
            return self._parse_summary(result_text, model, len(documents))

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._empty_summary(model, len(documents))

    async def generate_summary_async(
        self,
        documents: list[dict],
        model: Optional[str] = None,
    ) -> DocumentSummary:
        """Generate a summary from a sequence of documents with images.

        This method sends document images directly to Qwen-VL with timestamps,
        allowing the model to analyze the visual content alongside any text.

        Args:
            documents: List of document dicts with 'id', 'date', 'image', and optionally 'text' keys.
                      'image' can be PIL Image, file path, or bytes.
            model: Model to use (defaults to config value).

        Returns:
            DocumentSummary object.
        """
        model = model or self.config.summary.model

        # Sort documents by date
        sorted_docs = sort_by_date(documents, date_key="date")

        # Process in batches if needed
        if len(sorted_docs) > self.MAX_IMAGES_PER_CALL:
            return await self._generate_batched_summary_async(sorted_docs, model)

        # Build multimodal message with images and timestamps
        content = self._build_multimodal_content(sorted_docs)

        # Add the summary prompt at the end
        prompt = self.config.prompts.summary
        content.append({"type": "text", "text": prompt})

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": content}],
                ),
                timeout=self.timeout
            )

            result_text = completion.choices[0].message.content or ""
            return self._parse_summary(result_text, model, len(documents))

        except asyncio.TimeoutError:
            logger.error(f"Summary generation timed out after {self.timeout}s")
            return self._empty_summary(model, len(documents))
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._empty_summary(model, len(documents))

    def _build_multimodal_content(self, documents: list[dict]) -> list[dict]:
        """Build multimodal content array with images and timestamps.

        Args:
            documents: List of sorted document dicts.

        Returns:
            List of content items for Qwen-VL API.
        """
        content = []

        for doc in documents:
            date = doc.get("date", "Unknown date")
            doc_id = doc.get("id", "Unknown")
            text = doc.get("text", "")

            # Add timestamp/date marker
            timestamp_text = f"<{date}> Document: {doc_id}"
            if text:
                timestamp_text += f"\nTranscription: {text}"

            content.append({"type": "text", "text": timestamp_text})

            # Add image if present
            if "image" in doc and doc["image"] is not None:
                image_b64 = image_to_base64(doc["image"])
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                })

        return content

    async def _generate_batched_summary_async(
        self,
        documents: list[dict],
        model: str,
    ) -> DocumentSummary:
        """Generate summary for large document sets by batching.

        Args:
            documents: List of all documents.
            model: Model to use.

        Returns:
            Combined DocumentSummary.
        """
        batch_summaries = []

        # Process in batches
        for i in range(0, len(documents), self.MAX_IMAGES_PER_CALL):
            batch = documents[i:i + self.MAX_IMAGES_PER_CALL]
            batch_num = i // self.MAX_IMAGES_PER_CALL + 1
            total_batches = (len(documents) + self.MAX_IMAGES_PER_CALL - 1) // self.MAX_IMAGES_PER_CALL

            logger.info(f"Processing batch {batch_num}/{total_batches}")

            # Build content for this batch
            content = self._build_multimodal_content(batch)
            content.append({
                "type": "text",
                "text": f"Summarize these documents (batch {batch_num} of {total_batches}). "
                       f"Focus on key events, changes, and notable details."
            })

            try:
                completion = await asyncio.wait_for(
                    self.async_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": content}],
                    ),
                    timeout=self.timeout
                )

                text = completion.choices[0].message.content or ""
                batch_summaries.append(text)

            except asyncio.TimeoutError:
                logger.error(f"Batch {batch_num} timed out")
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")

        # Combine batch summaries with a final summary call
        if batch_summaries:
            return await self._combine_batch_summaries_async(batch_summaries, model, len(documents))

        return self._empty_summary(model, len(documents))

    async def _combine_batch_summaries_async(
        self,
        batch_summaries: list[str],
        model: str,
        doc_count: int,
    ) -> DocumentSummary:
        """Combine batch summaries into a final summary.

        Args:
            batch_summaries: List of batch summary texts.
            model: Model to use.
            doc_count: Total document count.

        Returns:
            Combined DocumentSummary.
        """
        combined_text = "\n\n---\n\n".join(
            f"## Batch {i+1} Summary\n\n{text}"
            for i, text in enumerate(batch_summaries)
        )

        combine_prompt = f"""The following are summaries of document batches from a larger collection.
Please synthesize these into a single coherent summary with:
- Timeline of key events
- Key changes and developments
- Research questions worth exploring

{combined_text}

{self.config.prompts.summary}"""

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": [{"type": "text", "text": combine_prompt}]}],
                ),
                timeout=self.timeout
            )

            result_text = completion.choices[0].message.content or ""
            return self._parse_summary(result_text, model, doc_count)

        except Exception as e:
            logger.error(f"Combining summaries failed: {e}")

        # Fallback: return parsed version of combined batch summaries
        return self._parse_summary(combined_text, model, doc_count)

    def _parse_summary(
        self,
        content: str,
        model: str,
        doc_count: int,
    ) -> DocumentSummary:
        """Parse the summary from LLM response.

        Args:
            content: LLM response content.
            model: Model used.
            doc_count: Number of documents processed.

        Returns:
            DocumentSummary object.
        """
        # Parse sections from markdown
        timeline = self._parse_timeline(content)
        key_changes = self._parse_key_changes(content)
        research_questions = self._parse_research_questions(content)

        return DocumentSummary(
            timeline=timeline,
            key_changes=key_changes,
            research_questions=research_questions,
            full_text=content,
            generated_at=datetime.utcnow().isoformat() + "Z",
            model=model,
            document_count=doc_count,
        )

    def _parse_timeline(self, content: str) -> list[dict]:
        """Parse timeline events from content."""
        events = []

        # Look for Timeline section
        timeline_match = re.search(
            r"##?\s*Timeline.*?\n(.*?)(?=##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if timeline_match:
            section = timeline_match.group(1)
            # Parse bullet points
            for line in section.split("\n"):
                line = line.strip()
                if line.startswith(("-", "*", "•")):
                    text = line.lstrip("-*• ").strip()
                    # Try to extract date
                    date_match = re.match(r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{4}[-/]\d{2}|\d{4})[:\s]*(.*)", text)
                    if date_match:
                        events.append({
                            "date": date_match.group(1),
                            "description": date_match.group(2).strip(),
                        })
                    else:
                        events.append({
                            "date": None,
                            "description": text,
                        })

        return events

    def _parse_key_changes(self, content: str) -> list[dict]:
        """Parse key changes from content."""
        changes = []

        changes_match = re.search(
            r"##?\s*Key Changes.*?\n(.*?)(?=##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if changes_match:
            section = changes_match.group(1)
            for line in section.split("\n"):
                line = line.strip()
                if line.startswith(("-", "*", "•")):
                    text = line.lstrip("-*• ").strip()
                    if text:
                        changes.append({"description": text})

        return changes

    def _parse_research_questions(self, content: str) -> list[str]:
        """Parse research questions from content."""
        questions = []

        questions_match = re.search(
            r"##?\s*Research Questions.*?\n(.*?)(?=##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if questions_match:
            section = questions_match.group(1)
            for line in section.split("\n"):
                line = line.strip()
                if line.startswith(("-", "*", "•", "1", "2", "3", "4", "5")):
                    text = line.lstrip("-*•0123456789.) ").strip()
                    if text and len(text) > 10:
                        questions.append(text)

        return questions

    def _empty_summary(self, model: str, doc_count: int) -> DocumentSummary:
        """Create an empty summary for error cases."""
        return DocumentSummary(
            timeline=[],
            key_changes=[],
            research_questions=[],
            full_text="",
            generated_at=datetime.utcnow().isoformat() + "Z",
            model=model,
            document_count=doc_count,
        )

    def generate_text_only_summary(
        self,
        documents: list[dict],
        model: Optional[str] = None,
    ) -> DocumentSummary:
        """Generate a summary from document text only (sync).

        Args:
            documents: List of document dicts with 'id', 'date', and 'text' keys.
            model: Model to use (defaults to config value).

        Returns:
            DocumentSummary object.
        """
        model = model or self.config.summary.model

        # Sort documents by date
        sorted_docs = sort_by_date(documents, date_key="date")

        # Format documents as text
        parts = []
        for i, doc in enumerate(sorted_docs, 1):
            date = doc.get("date", "Unknown date")
            doc_id = doc.get("id", f"Document {i}")
            text = doc.get("text", "")
            parts.append(f"### Document {i}: {doc_id} ({date})\n\n{text}\n")

        formatted_docs = "\n---\n\n".join(parts)

        # Build prompt
        prompt = f"{formatted_docs}\n\n{self.config.prompts.summary}"

        try:
            completion = self.sync_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            )

            result_text = completion.choices[0].message.content or ""
            return self._parse_summary(result_text, model, len(documents))

        except Exception as e:
            logger.error(f"Text-only summary generation failed: {e}")
            return self._empty_summary(model, len(documents))

    async def generate_text_only_summary_async(
        self,
        documents: list[dict],
        model: Optional[str] = None,
    ) -> DocumentSummary:
        """Generate a summary from document text only (no images).

        Use this method when images are not available or for faster processing.

        Args:
            documents: List of document dicts with 'id', 'date', and 'text' keys.
            model: Model to use (defaults to config value).

        Returns:
            DocumentSummary object.
        """
        model = model or self.config.summary.model

        # Sort documents by date
        sorted_docs = sort_by_date(documents, date_key="date")

        # Format documents as text
        parts = []
        for i, doc in enumerate(sorted_docs, 1):
            date = doc.get("date", "Unknown date")
            doc_id = doc.get("id", f"Document {i}")
            text = doc.get("text", "")
            parts.append(f"### Document {i}: {doc_id} ({date})\n\n{text}\n")

        formatted_docs = "\n---\n\n".join(parts)

        # Build prompt
        prompt = f"{formatted_docs}\n\n{self.config.prompts.summary}"

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                ),
                timeout=self.timeout
            )

            result_text = completion.choices[0].message.content or ""
            return self._parse_summary(result_text, model, len(documents))

        except asyncio.TimeoutError:
            logger.error(f"Text-only summary timed out after {self.timeout}s")
            return self._empty_summary(model, len(documents))
        except Exception as e:
            logger.error(f"Text-only summary generation failed: {e}")
            return self._empty_summary(model, len(documents))

    def save_summary(
        self,
        summary: DocumentSummary,
        output_dir: Path,
    ) -> dict[str, Path]:
        """Save summary to multiple files.

        Args:
            summary: DocumentSummary to save.
            output_dir: Directory to save to.

        Returns:
            Dictionary of file types to paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {}

        # Save full markdown
        full_path = output_dir / "full_summary.md"
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(f"# Document Collection Summary\n\n")
            f.write(f"Generated: {summary.generated_at}\n")
            f.write(f"Model: {summary.model}\n")
            f.write(f"Documents analyzed: {summary.document_count}\n\n")
            f.write("---\n\n")
            f.write(summary.full_text)
        paths["full_summary"] = full_path

        # Save timeline JSON
        timeline_path = output_dir / "timeline.json"
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(summary.timeline, f, indent=2, ensure_ascii=False)
        paths["timeline"] = timeline_path

        # Save key changes JSON
        changes_path = output_dir / "key_changes.json"
        with open(changes_path, "w", encoding="utf-8") as f:
            json.dump(summary.key_changes, f, indent=2, ensure_ascii=False)
        paths["key_changes"] = changes_path

        # Save research questions JSON
        questions_path = output_dir / "research_questions.json"
        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump(summary.research_questions, f, indent=2, ensure_ascii=False)
        paths["research_questions"] = questions_path

        logger.info(f"Saved summary to {output_dir}")
        return paths


def load_summary(output_dir: Path) -> DocumentSummary:
    """Load a summary from files.

    Args:
        output_dir: Directory containing summary files.

    Returns:
        DocumentSummary object.
    """
    # Load full summary
    full_path = output_dir / "full_summary.md"
    with open(full_path, encoding="utf-8") as f:
        full_text = f.read()

    # Load timeline
    timeline_path = output_dir / "timeline.json"
    with open(timeline_path, encoding="utf-8") as f:
        timeline = json.load(f)

    # Load key changes
    changes_path = output_dir / "key_changes.json"
    with open(changes_path, encoding="utf-8") as f:
        key_changes = json.load(f)

    # Load research questions
    questions_path = output_dir / "research_questions.json"
    with open(questions_path, encoding="utf-8") as f:
        research_questions = json.load(f)

    # Parse metadata from full text
    generated_match = re.search(r"Generated: (.+)", full_text)
    model_match = re.search(r"Model: (.+)", full_text)
    count_match = re.search(r"Documents analyzed: (\d+)", full_text)

    return DocumentSummary(
        timeline=timeline,
        key_changes=key_changes,
        research_questions=research_questions,
        full_text=full_text,
        generated_at=generated_match.group(1) if generated_match else "",
        model=model_match.group(1) if model_match else "",
        document_count=int(count_match.group(1)) if count_match else 0,
    )
