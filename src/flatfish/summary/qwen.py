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
        output_dir: Optional[Path] = None,
    ) -> DocumentSummary:
        """Generate a summary from a sequence of documents with images (sync).

        Args:
            documents: List of document dicts with 'id', 'date', 'image', and optionally 'text' keys.
            model: Model to use (defaults to config value).
            output_dir: Optional directory to save batch summaries for resume.

        Returns:
            DocumentSummary object.
        """
        model = model or self.config.summary.model

        # Sort documents by date
        sorted_docs = sort_by_date(documents, date_key="date")

        # Sample documents if there are too many
        sample_size = self.config.summary.sample_size
        if sample_size > 0 and len(sorted_docs) > sample_size:
            logger.info(f"Sampling {sample_size} documents from {len(sorted_docs)} total")
            # Take evenly spaced samples to cover the full date range
            step = len(sorted_docs) / sample_size
            indices = [int(i * step) for i in range(sample_size)]
            sorted_docs = [sorted_docs[i] for i in indices]

        # Process in batches if needed
        if len(sorted_docs) > self.MAX_IMAGES_PER_CALL:
            # For large batches, use async
            return asyncio.run(self._generate_batched_summary_async(sorted_docs, model, output_dir))

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

    # Track-specific prompts for focused extraction
    TRACK_PROMPTS = {
        "timeline": """Analyze these historical documents and extract a TIMELINE of events.

For each event, provide:
- The specific DATE (as precise as possible: year, month, day if available)
- A description of what happened

Output as a markdown table:
| Date | Event |
|------|-------|
| 1913-01-15 | Example event description |

Focus on CONCRETE, DATED events. Include births, deaths, transactions, travels, meetings, decisions.
Be specific with names, places, and dates. Extract ALL datable events you can identify.""",

        "key_changes": """Analyze these historical documents and identify KEY CHANGES over time.

Categorize changes as:
- **[Geographic]**: Moves, travels, relocations
- **[Occupational]**: Jobs, roles, career changes
- **[Social]**: Relationships, marriages, deaths, new connections
- **[Economic]**: Financial changes, property, business dealings
- **[Health]**: Medical events, conditions
- **[Political]**: Political involvement, historical context

Output as categorized bullet points:
- **[Category]**: Specific description of the change with names, dates, places

Focus on TRANSFORMATIONS and TRANSITIONS. What changed from one state to another?""",

        "research_questions": """Analyze these historical documents and generate RESEARCH QUESTIONS.

Generate doctoral-level, historiographically-engaged questions that:
1. Connect to broader historical debates and scholarship
2. Address silences, gaps, or tensions in the archive
3. Consider comparative frameworks (regional, national, transnational)
4. Probe methodological questions about using these sources
5. Explore intersections of race, class, gender, religion where relevant

Output as numbered questions with brief context:
1. QUESTION TEXT HERE
   WHY THIS MATTERS: Brief explanation of historiographical significance

Generate 5-10 substantive questions that a serious researcher would pursue.""",

        "narrative": """Analyze these historical documents and write a narrative summary.

Focus on:
1. WHO are the key people mentioned? (names, relationships, roles)
2. WHAT are the main activities, events, or themes?
3. WHERE does the action take place? (specific locations)
4. WHEN do key events occur? (date ranges, time periods)
5. What makes these documents DISTINCTIVE or unusual?

Write 2-4 paragraphs highlighting the most significant and interesting findings.
Prioritize concrete details over general observations."""
    }

    async def _generate_batched_summary_async(
        self,
        documents: list[dict],
        model: str,
        output_dir: Optional[Path] = None,
    ) -> DocumentSummary:
        """Generate summary for large document sets using track-based batching.

        Instead of asking each batch for everything, we run 4 parallel sessions
        per batch - one for each track (timeline, key_changes, research_questions, narrative).
        This ensures we get focused, high-quality data for each track.

        Args:
            documents: List of all documents.
            model: Model to use.
            output_dir: Optional directory to save batch summaries.

        Returns:
            Combined DocumentSummary.
        """
        total_batches = (len(documents) + self.MAX_IMAGES_PER_CALL - 1) // self.MAX_IMAGES_PER_CALL
        
        # Create track-specific directories if output_dir provided
        track_dirs = {}
        if output_dir:
            for track in ["timeline", "key_changes", "research_questions", "narrative"]:
                track_dir = output_dir / "batches" / track
                track_dir.mkdir(parents=True, exist_ok=True)
                track_dirs[track] = track_dir

        # Collect results per track
        track_results = {
            "timeline": [],
            "key_changes": [],
            "research_questions": [],
            "narrative": []
        }

        # Process each batch with all 4 tracks in parallel
        for i in range(0, len(documents), self.MAX_IMAGES_PER_CALL):
            batch = documents[i:i + self.MAX_IMAGES_PER_CALL]
            batch_num = i // self.MAX_IMAGES_PER_CALL + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} (4 tracks)")
            print(f"  Processing batch {batch_num}/{total_batches} (4 parallel tracks)...", flush=True)

            # Build content for this batch (reused across all tracks)
            base_content = self._build_multimodal_content(batch)
            
            # Create tasks for all 4 tracks
            tasks = []
            tracks_to_process = []
            
            for track in ["timeline", "key_changes", "research_questions", "narrative"]:
                # Check if this track's batch already exists
                if track in track_dirs:
                    batch_file = track_dirs[track] / f"batch_{batch_num:03d}.md"
                    if batch_file.exists():
                        existing = batch_file.read_text(encoding="utf-8")
                        track_results[track].append(existing)
                        continue
                
                # Create task for this track
                content = base_content.copy()
                content.append({
                    "type": "text",
                    "text": f"Batch {batch_num} of {total_batches}.\n\n{self.TRACK_PROMPTS[track]}"
                })
                
                task = self._process_track_batch(content, model, track, batch_num, track_dirs.get(track))
                tasks.append(task)
                tracks_to_process.append(track)
            
            # Run all track tasks in parallel
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for track, result in zip(tracks_to_process, results):
                    if isinstance(result, Exception):
                        logger.error(f"Batch {batch_num} {track} failed: {result}")
                    elif result:
                        track_results[track].append(result)

        # Combine results from each track
        print(f"  Combining {total_batches} batches across 4 tracks...", flush=True)
        return await self._combine_track_results(track_results, model, len(documents))

    async def _process_track_batch(
        self,
        content: list[dict],
        model: str,
        track: str,
        batch_num: int,
        track_dir: Optional[Path],
    ) -> Optional[str]:
        """Process a single track for a single batch.

        Args:
            content: Multimodal content with track-specific prompt.
            model: Model to use.
            track: Track name.
            batch_num: Batch number.
            track_dir: Directory to save results.

        Returns:
            Track result text or None on failure.
        """
        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": content}],
                ),
                timeout=self.timeout
            )

            text = completion.choices[0].message.content or ""
            
            # Save to file if track_dir provided
            if track_dir:
                batch_file = track_dir / f"batch_{batch_num:03d}.md"
                batch_file.write_text(text, encoding="utf-8")
                logger.info(f"Saved {track} batch {batch_num}")
            
            return text

        except asyncio.TimeoutError:
            logger.error(f"Track {track} batch {batch_num} timed out")
            return None
        except Exception as e:
            logger.error(f"Track {track} batch {batch_num} failed: {e}")
            return None

    async def _combine_track_results(
        self,
        track_results: dict[str, list[str]],
        model: str,
        doc_count: int,
    ) -> DocumentSummary:
        """Combine results from all tracks into final summary.

        Args:
            track_results: Dict mapping track name to list of batch results.
            model: Model to use.
            doc_count: Total document count.

        Returns:
            Combined DocumentSummary.
        """
        # Run all 4 combination tasks in parallel
        print(f"  Combining timeline events...", flush=True)
        print(f"  Combining key changes...", flush=True)
        print(f"  Combining research questions...", flush=True)
        print(f"  Generating narrative summary...", flush=True)
        
        timeline_task = self._combine_timeline_track(track_results["timeline"], model)
        changes_task = self._combine_key_changes_track(track_results["key_changes"], model)
        questions_task = self._combine_research_questions_track(track_results["research_questions"], model)
        narrative_task = self._generate_narrative_summary(track_results["narrative"], model, doc_count)
        
        timeline, key_changes, research_questions, narrative = await asyncio.gather(
            timeline_task, changes_task, questions_task, narrative_task
        )
        
        # Compose the full text
        full_text = self._compose_full_summary(narrative, timeline, key_changes, research_questions)
        
        return DocumentSummary(
            timeline=timeline,
            key_changes=key_changes,
            research_questions=research_questions,
            full_text=full_text,
            generated_at=datetime.utcnow().isoformat() + "Z",
            model=model,
            document_count=doc_count,
        )

    async def _combine_batch_summaries_async(
        self,
        batch_summaries: list[str],
        model: str,
        doc_count: int,
    ) -> DocumentSummary:
        """Combine batch summaries into a final summary using track-based approach.

        NOTE: This method is kept for backwards compatibility with old-style batch files.
        New code uses _combine_track_results instead.


        Instead of recursively summarizing (which loses distinctive details),
        we extract and combine each track separately:
        - Timeline events (merged and deduplicated)
        - Key changes (collected and categorized)
        - Research questions (collected and prioritized)
        - Narrative summary (distinctive highlights only)

        Args:
            batch_summaries: List of batch summary texts.
            model: Model to use.
            doc_count: Total document count.

        Returns:
            Combined DocumentSummary.
        """
        print(f"  Combining {len(batch_summaries)} batches using track-based approach...", flush=True)
        
        # Track 1: Extract and combine timeline events
        print(f"  Track 1/4: Extracting timeline events...", flush=True)
        timeline = await self._combine_timeline_track(batch_summaries, model)
        
        # Track 2: Extract and combine key changes
        print(f"  Track 2/4: Extracting key changes...", flush=True)
        key_changes = await self._combine_key_changes_track(batch_summaries, model)
        
        # Track 3: Extract and combine research questions
        print(f"  Track 3/4: Extracting research questions...", flush=True)
        research_questions = await self._combine_research_questions_track(batch_summaries, model)
        
        # Track 4: Generate narrative summary highlighting distinctive findings
        print(f"  Track 4/4: Generating narrative summary...", flush=True)
        narrative = await self._generate_narrative_summary(batch_summaries, model, doc_count)
        
        # Compose the full text
        full_text = self._compose_full_summary(narrative, timeline, key_changes, research_questions)
        
        return DocumentSummary(
            timeline=timeline,
            key_changes=key_changes,
            research_questions=research_questions,
            full_text=full_text,
            generated_at=datetime.utcnow().isoformat() + "Z",
            model=model,
            document_count=doc_count,
        )

    # Maximum characters per API call (roughly 20K tokens at ~4 chars/token)
    MAX_COMBINE_CHARS = 80000
    # Number of batches to combine in each hierarchical pass
    COMBINE_CHUNK_SIZE = 50

    async def _hierarchical_combine(
        self,
        texts: list[str],
        model: str,
        combine_prompt: str,
    ) -> str:
        """Hierarchically combine texts that exceed context limits.
        
        Recursively combines texts in chunks until the result fits in context.
        
        Args:
            texts: List of text chunks to combine.
            model: Model to use.
            combine_prompt: Prompt template with {content} placeholder.
            
        Returns:
            Combined result text.
        """
        # Base case: if texts fit in context, combine directly
        combined = "\n\n".join(texts)
        if len(combined) <= self.MAX_COMBINE_CHARS:
            prompt = combine_prompt.format(content=combined)
            try:
                completion = await asyncio.wait_for(
                    self.async_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                    ),
                    timeout=self.timeout
                )
                return completion.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"Combine failed: {e}")
                return combined  # Return raw content as fallback
        
        # Recursive case: combine in chunks
        logger.info(f"Hierarchical combine: {len(texts)} texts, {len(combined)} chars")
        print(f"    (combining {len(texts)} chunks hierarchically...)", flush=True)
        
        chunk_results = []
        for i in range(0, len(texts), self.COMBINE_CHUNK_SIZE):
            chunk = texts[i:i + self.COMBINE_CHUNK_SIZE]
            chunk_text = "\n\n".join(chunk)
            
            # If even a single chunk is too large, truncate it
            if len(chunk_text) > self.MAX_COMBINE_CHARS:
                chunk_text = chunk_text[:self.MAX_COMBINE_CHARS]
            
            prompt = combine_prompt.format(content=chunk_text)
            try:
                completion = await asyncio.wait_for(
                    self.async_client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                    ),
                    timeout=self.timeout
                )
                result = completion.choices[0].message.content or ""
                chunk_results.append(result)
            except Exception as e:
                logger.error(f"Chunk combine failed: {e}")
                # Keep some raw content as fallback
                chunk_results.append(chunk_text[:5000])
        
        # Recursively combine the chunk results
        if len(chunk_results) > 1:
            return await self._hierarchical_combine(chunk_results, model, combine_prompt)
        elif chunk_results:
            return chunk_results[0]
        else:
            return ""

    async def _combine_timeline_track(
        self,
        batch_summaries: list[str],
        model: str,
    ) -> list[dict]:
        """Extract and combine timeline events from all batches.
        
        Works with both:
        - New track-specific batches (already timeline-focused)
        - Old-style batches (need section extraction)
        """
        if not batch_summaries:
            return []
        
        # Collect all timeline content
        all_events_text = []
        for i, batch in enumerate(batch_summaries):
            # Check if this looks like old-style batch with sections
            timeline_match = re.search(
                r"##?\s*\*?\*?Timeline.*?\n(.*?)(?=##|\Z)",
                batch,
                re.IGNORECASE | re.DOTALL,
            )
            if timeline_match:
                all_events_text.append(f"Batch {i+1}:\n{timeline_match.group(1).strip()}")
            else:
                # Assume it's a track-specific batch - use whole content
                all_events_text.append(f"Batch {i+1}:\n{batch.strip()}")
        
        if not all_events_text:
            return []
        
        combine_prompt = """Below are timeline events extracted from multiple document batches.
Create a unified, chronological timeline by:
1. Merging duplicate or overlapping events
2. Keeping the MOST SPECIFIC details (names, places, exact dates)
3. Preserving distinctive/unusual events even if they seem minor
4. Using a markdown table format: | Date | Event |

Focus on CONCRETE, VERIFIABLE facts. Avoid generic descriptions.

{content}

Output a markdown table with | Date | Event | columns:"""

        try:
            result = await self._hierarchical_combine(all_events_text, model, combine_prompt)
            return self._parse_timeline(result)
        except Exception as e:
            logger.error(f"Timeline combination failed: {e}")
            # Fallback: parse events from raw batches
            all_events = []
            for batch in batch_summaries:
                all_events.extend(self._parse_timeline(batch))
            return all_events

    async def _combine_key_changes_track(
        self,
        batch_summaries: list[str],
        model: str,
    ) -> list[dict]:
        """Extract and categorize key changes from all batches.
        
        Works with both:
        - New track-specific batches (already key-changes-focused)
        - Old-style batches (need section extraction)
        """
        if not batch_summaries:
            return []
        
        # Collect all key changes content
        all_changes_text = []
        for i, batch in enumerate(batch_summaries):
            # Check if this looks like old-style batch with sections
            changes_match = re.search(
                r"##?\s*\*?\*?Key Changes.*?\n(.*?)(?=##|\Z)",
                batch,
                re.IGNORECASE | re.DOTALL,
            )
            if changes_match:
                all_changes_text.append(f"Batch {i+1}:\n{changes_match.group(1).strip()}")
            else:
                # Assume it's a track-specific batch - use whole content
                all_changes_text.append(f"Batch {i+1}:\n{batch.strip()}")
        
        if not all_changes_text:
            return []
        
        combine_prompt = """Below are "key changes" identified across multiple document batches.
Synthesize these into a categorized list of the most significant changes:

Categories to consider:
- Geographic/Location changes (moves, travels, relocations)
- Occupational/Professional changes (jobs, roles, responsibilities)
- Social/Relationship changes (marriages, deaths, new connections)
- Economic changes (financial status, property, business)
- Health/Personal changes
- Political/Historical context changes

For each change, provide:
1. Category type
2. Specific description with names, dates, and places

Focus on DISTINCTIVE changes that tell a story. Avoid generic observations.

{content}

Output as bullet points with category labels:
- **[Category]**: Description of specific change"""

        try:
            result = await self._hierarchical_combine(all_changes_text, model, combine_prompt)
            return self._parse_key_changes(result)
        except Exception as e:
            logger.error(f"Key changes combination failed: {e}")
            all_changes = []
            for batch in batch_summaries:
                all_changes.extend(self._parse_key_changes(batch))
            return all_changes

    async def _combine_research_questions_track(
        self,
        batch_summaries: list[str],
        model: str,
    ) -> list[str]:
        """Extract and prioritize research questions from all batches.
        
        Works with both:
        - New track-specific batches (already research-questions-focused)
        - Old-style batches (need section extraction)
        """
        if not batch_summaries:
            return []
        
        # Collect all research questions content
        all_questions_text = []
        for i, batch in enumerate(batch_summaries):
            # Check if this looks like old-style batch with sections
            questions_match = re.search(
                r"##?\s*\*?\*?Research Questions.*?\n(.*?)(?=##|\Z)",
                batch,
                re.IGNORECASE | re.DOTALL,
            )
            if questions_match:
                all_questions_text.append(questions_match.group(1).strip())
            else:
                # Assume it's a track-specific batch - use whole content
                all_questions_text.append(batch.strip())
        
        if not all_questions_text:
            return []
        
        combine_prompt = """You are a senior historian helping to identify significant research questions 
for a scholarly project. Based on the preliminary questions below (generated from document analysis), 
synthesize and elevate these into 10-15 research questions suitable for:

- A doctoral dissertation prospectus
- A peer-reviewed journal article
- A scholarly monograph proposal
- A major grant application (NEH, ACLS, Mellon)

Your questions should demonstrate:

1. **HISTORIOGRAPHICAL ENGAGEMENT**: Frame questions in terms of existing scholarly debates. 
   Use language like "How does this complicate/confirm/challenge our understanding of..."
   Reference relevant historical frameworks (labor history, environmental history, 
   history of capitalism, transnational history, history of science, etc.)

2. **METHODOLOGICAL SOPHISTICATION**: Consider questions about source criticism, 
   archival silences, whose voices are present/absent, how documents were produced and preserved.

3. **COMPARATIVE & TRANSNATIONAL FRAMING**: Suggest connections beyond the immediate context.
   How does this relate to parallel developments elsewhere? What networks/circulations are visible?

4. **INTERDISCIPLINARY CONNECTIONS**: Consider angles from anthropology, sociology, 
   geography, environmental studies, science & technology studies where relevant.

5. **THEORETICAL DEPTH**: Engage with concepts like agency, power, knowledge production,
   spatial analysis, periodization, causation vs. contingency.

AVOID:
- Basic "what happened" questions
- Questions answerable with a simple fact
- Generic questions that could apply to any archive
- Questions that don't engage with "so what?" significance

Preliminary questions from document analysis:
{content}

Generate 10-15 doctoral-level research questions, each 2-3 sentences explaining the question's 
significance and how this collection might address it:"""

        try:
            result = await self._hierarchical_combine(all_questions_text, model, combine_prompt)
            return self._parse_research_questions(result)
        except Exception as e:
            logger.error(f"Research questions combination failed: {e}")
            all_questions = []
            for batch in batch_summaries:
                all_questions.extend(self._parse_research_questions(batch))
            return list(set(all_questions))[:15]  # Dedupe and limit

    async def _generate_narrative_summary(
        self,
        batch_summaries: list[str],
        model: str,
        doc_count: int,
    ) -> str:
        """Generate a professional archival finding aid summary."""
        if not batch_summaries:
            return f"This collection contains {doc_count} documents."
        
        # For large batch sets, first summarize batches hierarchically
        # to extract key entities (names, places, dates, themes)
        if len(batch_summaries) > 50:
            # Extract key info from batches in chunks
            extraction_prompt = """Summarize these document descriptions, extracting:
1. Names of people mentioned (with roles/relationships)
2. Places mentioned
3. Date ranges
4. Key themes and activities
5. Notable or unusual details

Be concise but preserve specific details.

{content}

Key information:"""
            
            print(f"    (extracting key info from {len(batch_summaries)} narrative batches...)", flush=True)
            context = await self._hierarchical_combine(batch_summaries, model, extraction_prompt)
        else:
            # For smaller sets, use batch intros directly
            batch_intros = []
            for i, batch in enumerate(batch_summaries):
                intro = batch.split('\n')[0:8]
                batch_intros.append(f"Batch {i+1}: " + " ".join(intro))
            context = "\n".join(batch_intros)
        
        # Truncate if still too long
        MAX_CHARS = self.MAX_COMBINE_CHARS
        if len(context) > MAX_CHARS:
            context = context[:MAX_CHARS]
        
        prompt = f"""You are a professional archivist writing a finding aid for a collection of {doc_count} documents.
Based on the document summaries below, write a comprehensive collection description following 
the DACS (Describing Archives: A Content Standard) format used by professional archives.

Your finding aid should include these sections:

## Collection Overview
- **Creator**: Identify the person(s) who created these documents. Include full name, 
  life dates if determinable, occupation/profession, and their significance.
- **Title**: A descriptive title for the collection
- **Dates**: Inclusive dates (earliest to latest) and bulk dates (period of heaviest documentation)
- **Extent**: Approximately {doc_count} documents
- **Abstract**: A 2-3 sentence summary of the collection's contents and significance

## Biographical/Historical Note
Write 2-3 paragraphs providing context about the creator(s):
- Life history, career, significant accomplishments
- Historical context of the time period
- Why these documents were created and preserved
- Connections to broader historical events or movements

## Scope and Content
Write 2-3 paragraphs describing:
- Types of documents in the collection (diaries, letters, business records, etc.)
- Major topics, themes, and subjects covered
- Geographic locations mentioned
- Key individuals, organizations, or events documented
- Any notable or unusual items

## Historical Significance
Explain in 1-2 paragraphs:
- What makes this collection valuable for historical research
- What aspects of history it documents (social, economic, political, cultural)
- How it contributes to our understanding of the period/place/topic
- What perspectives or voices it represents

## Related Materials
Suggest (based on content):
- Types of related collections that might exist elsewhere
- Secondary sources or published works that might relate to this collection
- Other archives or repositories that might hold complementary materials

Be specific and detailed. Use the actual names, places, dates, and events from the documents.
Avoid generic language. Write in a professional, scholarly tone.

Document summaries for analysis:
{context}

Write the finding aid:"""

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
                ),
                timeout=self.timeout * 2  # Allow more time for detailed response
            )
            return completion.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Finding aid generation failed: {e}")
            return f"This collection contains {doc_count} documents. See the timeline, key changes, and research questions below for details."

    def _compose_full_summary(
        self,
        narrative: str,
        timeline: list[dict],
        key_changes: list[dict],
        research_questions: list[str],
    ) -> str:
        """Compose the full summary markdown from individual tracks."""
        sections = [narrative, "\n\n"]
        
        # Timeline section
        if timeline:
            sections.append("## Timeline of Key Events\n\n")
            sections.append("| Date | Event |\n|------|-------|\n")
            for event in timeline:
                date = event.get("date", "Unknown")
                desc = event.get("description", "").replace("|", "—")
                sections.append(f"| {date} | {desc} |\n")
            sections.append("\n")
        
        # Key changes section
        if key_changes:
            sections.append("## Key Changes Across Documents\n\n")
            for change in key_changes:
                change_type = change.get("type", "General")
                desc = change.get("description", "")
                if change_type:
                    sections.append(f"- **{change_type}**: {desc}\n")
                else:
                    sections.append(f"- {desc}\n")
            sections.append("\n")
        
        # Research questions section
        if research_questions:
            sections.append("## Research Questions\n\n")
            for i, question in enumerate(research_questions, 1):
                sections.append(f"{i}. {question}\n")
        
        return "".join(sections)

    async def _combine_small_batch_async(
        self,
        batch_summaries: list[str],
        model: str,
        doc_count: int = 0,
    ) -> str | DocumentSummary:
        """Combine a small number of batch summaries.
        
        Returns string if doc_count is 0 (intermediate), DocumentSummary if final.
        """
        combined_text = "\n\n---\n\n".join(
            f"## Batch {i+1} Summary\n\n{text}"
            for i, text in enumerate(batch_summaries)
        )
        
        # Truncate if still too long (rough estimate: 4 chars per token, limit ~100k tokens)
        MAX_CHARS = 400000
        if len(combined_text) > MAX_CHARS:
            logger.warning(f"Combined text too long ({len(combined_text)} chars), truncating...")
            combined_text = combined_text[:MAX_CHARS] + "\n\n[... truncated due to length ...]"

        combine_prompt = f"""The following are summaries of document batches from a larger collection.
Synthesize these while PRESERVING DISTINCTIVE DETAILS:
- Keep specific names, dates, places, and amounts
- Highlight unusual or unexpected findings
- Note contradictions or gaps in the record

Include:
## Timeline of Key Events (as markdown table)
## Key Changes (categorized bullet points)  
## Research Questions (numbered list of specific questions)

{combined_text}"""

        try:
            completion = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": [{"type": "text", "text": combine_prompt}]}],
                ),
                timeout=self.timeout
            )

            result_text = completion.choices[0].message.content or ""
            
            # Return string for intermediate, DocumentSummary for final
            if doc_count == 0:
                return result_text
            return self._parse_summary(result_text, model, doc_count)

        except Exception as e:
            logger.error(f"Combining summaries failed: {e}")

        # Fallback: return parsed version of combined batch summaries
        if doc_count == 0:
            return combined_text
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
        """Parse timeline events from content.
        
        Handles both:
        - Content with ## Timeline section header
        - Raw markdown tables or bullet points without headers
        """
        events = []

        # Look for Timeline section
        timeline_match = re.search(
            r"##?\s*\*?\*?Timeline.*?\n(.*?)(?=##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if timeline_match:
            section = timeline_match.group(1)
        else:
            # No header found - use the whole content (for track-specific batches)
            section = content
            
        # Check if it's a markdown table format
        if "|" in section:
            # Parse table rows
            for line in section.split("\n"):
                line = line.strip()
                # Skip header separator line (|---|---|) and header row (| Date | Event |)
                if line.startswith("|") and "---" not in line:
                    # Split by | and clean up
                    parts = [p.strip() for p in line.split("|")]
                    # Filter out empty parts (from leading/trailing |)
                    parts = [p for p in parts if p]
                    if len(parts) >= 2:
                        date_part = parts[0].strip("*").strip()
                        desc_part = parts[1].strip()
                        # Skip header row
                        if date_part.lower() in ("date", "dates") and desc_part.lower() in ("event", "events", "description"):
                            continue
                        if date_part and desc_part:
                            events.append({
                                "date": date_part,
                                "description": desc_part,
                            })
        else:
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
        """Parse key changes from content.
        
        Handles both:
        - Content with ## Key Changes section header
        - Raw bullet points without headers
        """
        changes = []

        changes_match = re.search(
            r"##?\s*\*?\*?Key Changes.*?\n(.*?)(?=###\s*\*?\*?Research|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if changes_match:
            section = changes_match.group(1)
        else:
            # No header found - use the whole content (for track-specific batches)
            section = content
            
        current_type = None
        
        for line in section.split("\n"):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for subheading (#### **1. Shift in Role**)
            heading_match = re.match(r"#{1,4}\s*\*?\*?\d*\.?\s*(.+?)\*?\*?\s*$", line)
            if heading_match:
                current_type = heading_match.group(1).strip("* ")
                continue
            
            # Check for **[Category]**: format (category header with optional description)
            category_match = re.match(r"-\s*\*\*\[?([^\]:\*]+)\]?\*\*:?\s*(.*)", line)
            if category_match:
                current_type = category_match.group(1).strip()
                desc = category_match.group(2).strip()
                if desc and len(desc) > 5:
                    changes.append({
                        "type": current_type,
                        "description": desc
                    })
                continue
            
            # Parse bullet points (including indented ones)
            if line.startswith(("-", "*", "•")) and not line.startswith("**"):
                text = line.lstrip("-*• ").strip()
                if text and len(text) > 5:
                    changes.append({
                        "type": current_type,
                        "description": text
                    })

        return changes

    def _parse_research_questions(self, content: str) -> list[str]:
        """Parse research questions from content.
        
        Handles both:
        - Content with ## Research Questions section header
        - Raw numbered list or bullet points without headers
        - Bold formatted questions (1. **Question**)
        """
        questions = []

        questions_match = re.search(
            r"##?\s*Research Questions.*?\n(.*?)(?=##|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )

        if questions_match:
            section = questions_match.group(1)
        else:
            # No header found - use the whole content (for track-specific batches)
            section = content
        
        # Try to extract bold questions first (e.g., "1. **Question text**")
        bold_questions = re.findall(
            r'^\d+\.\s*\*\*(.+?)\*\*',
            section,
            re.MULTILINE
        )
        
        if bold_questions:
            for q in bold_questions:
                q = q.strip()
                if q and len(q) > 10:
                    questions.append(q)
        else:
            # Fallback to line-by-line parsing
            for line in section.split("\n"):
                line = line.strip()
                if line.startswith(("-", "*", "•", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                    # Strip leading markers and bold formatting
                    text = line.lstrip("-*•0123456789.) ").strip()
                    text = text.strip("*").strip()  # Remove bold markers
                    if text and len(text) > 10:
                        questions.append(text)

        return questions

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

    def combine_batches(
        self,
        output_dir: Path,
        model: Optional[str] = None,
    ) -> DocumentSummary:
        """Combine existing batch summaries into a final summary.

        Supports both:
        - New track-based structure: batches/{timeline,key_changes,research_questions,narrative}/batch_*.md
        - Old flat structure: batches/batch_*.md

        Args:
            output_dir: Directory containing batches/ subdirectory.
            model: Model to use for combining.

        Returns:
            Combined DocumentSummary.
        """
        model = model or self.config.summary.model
        batches_dir = output_dir / "batches"
        
        if not batches_dir.exists():
            raise ValueError(f"No batches directory found at {batches_dir}")
        
        # Check for new track-based structure
        track_dirs = {
            "timeline": batches_dir / "timeline",
            "key_changes": batches_dir / "key_changes",
            "research_questions": batches_dir / "research_questions",
            "narrative": batches_dir / "narrative",
        }
        
        has_track_dirs = any(d.exists() for d in track_dirs.values())
        
        if has_track_dirs:
            # New track-based structure
            track_results = {}
            doc_count = 0
            
            for track_name, track_dir in track_dirs.items():
                if track_dir.exists():
                    batch_files = sorted(track_dir.glob("batch_*.md"))
                    print(f"Loading {len(batch_files)} {track_name} batches...", flush=True)
                    track_results[track_name] = [bf.read_text(encoding="utf-8") for bf in batch_files]
                    doc_count = max(doc_count, len(batch_files) * self.MAX_IMAGES_PER_CALL)
                else:
                    track_results[track_name] = []
            
            print(f"Combining batch summaries using track-based approach...", flush=True)
            return asyncio.run(self._combine_track_results(track_results, model, doc_count))
        else:
            # Old flat structure - fall back to legacy combining
            batch_files = sorted(batches_dir.glob("batch_*.md"))
            if not batch_files:
                raise ValueError(f"No batch files found in {batches_dir}")
            
            print(f"Loading {len(batch_files)} batch summaries...", flush=True)
            batch_summaries = []
            for bf in batch_files:
                batch_summaries.append(bf.read_text(encoding="utf-8"))
            
            # Count documents (estimate from batch count)
            doc_count = len(batch_files) * self.MAX_IMAGES_PER_CALL
            
            print(f"Combining batch summaries...", flush=True)
            return asyncio.run(self._combine_batch_summaries_async(batch_summaries, model, doc_count))

    def save_summary(
        self,
        summary: DocumentSummary,
        output_dir: Path,
    ) -> dict[str, Path]:
        """Save summary to multiple files (both JSON and editable text).

        Args:
            summary: DocumentSummary to save.
            output_dir: Directory to save to.

        Returns:
            Dictionary of file types to paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {}

        # Save full markdown (finding aid)
        full_path = output_dir / "finding_aid.md"
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(f"# Collection Finding Aid\n\n")
            f.write(f"Generated: {summary.generated_at}\n")
            f.write(f"Model: {summary.model}\n")
            f.write(f"Documents analyzed: {summary.document_count}\n\n")
            f.write("---\n\n")
            f.write(summary.full_text)
        paths["finding_aid"] = full_path

        # Save timeline as editable text file
        timeline_txt_path = output_dir / "timeline.txt"
        with open(timeline_txt_path, "w", encoding="utf-8") as f:
            f.write("# Timeline of Events\n")
            f.write("# Format: DATE | EVENT DESCRIPTION\n")
            f.write("# Edit this file to correct or add events. One event per line.\n")
            f.write("# Lines starting with # are comments and will be ignored.\n\n")
            for event in summary.timeline:
                date = event.get("date", "Unknown")
                desc = event.get("description", "").replace("|", "-")
                f.write(f"{date} | {desc}\n")
        paths["timeline_txt"] = timeline_txt_path

        # Save key changes as editable text file
        changes_txt_path = output_dir / "key_changes.txt"
        with open(changes_txt_path, "w", encoding="utf-8") as f:
            f.write("# Key Changes Across Documents\n")
            f.write("# Format: [CATEGORY] Description of change\n")
            f.write("# Categories: Geographic, Occupational, Social, Economic, Health, Political, General\n")
            f.write("# Edit this file to correct or add changes. One change per line.\n")
            f.write("# Lines starting with # are comments and will be ignored.\n\n")
            for change in summary.key_changes:
                change_type = change.get("type", "General")
                desc = change.get("description", "")
                f.write(f"[{change_type}] {desc}\n")
        paths["key_changes_txt"] = changes_txt_path

        # Save research questions as editable text file
        questions_txt_path = output_dir / "research_questions.txt"
        with open(questions_txt_path, "w", encoding="utf-8") as f:
            f.write("# Research Questions\n")
            f.write("# One question per paragraph. Blank lines separate questions.\n")
            f.write("# Edit this file to refine, add, or remove questions.\n")
            f.write("# Lines starting with # are comments and will be ignored.\n\n")
            for i, question in enumerate(summary.research_questions, 1):
                f.write(f"{question}\n\n")
        paths["research_questions_txt"] = questions_txt_path

        # Also save JSON versions for backwards compatibility
        timeline_path = output_dir / "timeline.json"
        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump(summary.timeline, f, indent=2, ensure_ascii=False)
        paths["timeline"] = timeline_path

        changes_path = output_dir / "key_changes.json"
        with open(changes_path, "w", encoding="utf-8") as f:
            json.dump(summary.key_changes, f, indent=2, ensure_ascii=False)
        paths["key_changes"] = changes_path

        questions_path = output_dir / "research_questions.json"
        with open(questions_path, "w", encoding="utf-8") as f:
            json.dump(summary.research_questions, f, indent=2, ensure_ascii=False)
        paths["research_questions"] = questions_path

        # Keep old filename for compatibility
        old_full_path = output_dir / "full_summary.md"
        with open(old_full_path, "w", encoding="utf-8") as f:
            f.write(f"# Document Collection Summary\n\n")
            f.write(f"Generated: {summary.generated_at}\n")
            f.write(f"Model: {summary.model}\n")
            f.write(f"Documents analyzed: {summary.document_count}\n\n")
            f.write("---\n\n")
            f.write(summary.full_text)
        paths["full_summary"] = old_full_path

        logger.info(f"Saved summary to {output_dir}")
        return paths


def load_summary(output_dir: Path) -> DocumentSummary:
    """Load a summary from files.

    Prefers editable text files (.txt) over JSON files if they exist,
    allowing users to make corrections that will be reflected in the site.

    Args:
        output_dir: Directory containing summary files.

    Returns:
        DocumentSummary object.
    """
    # Load full summary / finding aid
    # Prefer the editable text file
    finding_aid_txt = output_dir / "finding_aid.txt"
    full_path = output_dir / "full_summary.md"
    
    if finding_aid_txt.exists():
        with open(finding_aid_txt, encoding="utf-8") as f:
            full_text = f.read()
        # Remove the editing instructions header if present
        if full_text.startswith("# ARCHIVAL FINDING AID"):
            # Find the actual content after the instructions
            lines = full_text.split("\n")
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith("---") and i > 0:
                    content_start = i + 1
                    break
            full_text = "\n".join(lines[content_start:]).strip()
    elif full_path.exists():
        with open(full_path, encoding="utf-8") as f:
            full_text = f.read()
    else:
        full_text = ""

    # Load timeline - prefer text file
    timeline_txt = output_dir / "timeline.txt"
    timeline_json = output_dir / "timeline.json"
    timeline = []
    
    if timeline_txt.exists():
        with open(timeline_txt, encoding="utf-8") as f:
            content = f.read()
        # Parse the text format: DATE | DESCRIPTION
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---"):
                continue
            if "|" in line:
                parts = line.split("|", 1)
                if len(parts) == 2:
                    date = parts[0].strip()
                    description = parts[1].strip()
                    if date and description:
                        timeline.append({
                            "date": date,
                            "event": description,
                            "source": ""  # Source info not preserved in text format
                        })
    elif timeline_json.exists():
        with open(timeline_json, encoding="utf-8") as f:
            timeline = json.load(f)

    # Load key changes - prefer text file
    changes_txt = output_dir / "key_changes.txt"
    changes_json = output_dir / "key_changes.json"
    key_changes = []
    
    if changes_txt.exists():
        with open(changes_txt, encoding="utf-8") as f:
            content = f.read()
        # Parse the text format: [CATEGORY] Description
        category_pattern = re.compile(r"^\[([^\]]+)\]\s*(.+)$")
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("---"):
                continue
            match = category_pattern.match(line)
            if match:
                category = match.group(1).strip()
                description = match.group(2).strip()
                key_changes.append({
                    "category": category,
                    "description": description,
                    "source": ""  # Source info not preserved in text format
                })
    elif changes_json.exists():
        with open(changes_json, encoding="utf-8") as f:
            key_changes = json.load(f)

    # Load research questions - prefer text file
    questions_txt = output_dir / "research_questions.txt"
    questions_json = output_dir / "research_questions.json"
    research_questions = []
    
    if questions_txt.exists():
        with open(questions_txt, encoding="utf-8") as f:
            content = f.read()
        # Parse the numbered format: 1. QUESTION
        # and look for "   WHY THIS MATTERS:" lines
        current_question = None
        current_context = []
        
        for line in content.split("\n"):
            if line.startswith("#") or line.startswith("---"):
                continue
            
            # Check for numbered question
            q_match = re.match(r"^\d+\.\s+(.+)$", line)
            if q_match:
                # Save previous question if exists
                if current_question:
                    research_questions.append({
                        "question": current_question,
                        "context": " ".join(current_context).strip(),
                        "source": ""
                    })
                current_question = q_match.group(1).strip()
                current_context = []
            elif line.strip().startswith("WHY THIS MATTERS:"):
                # This is the context line
                context = line.strip().replace("WHY THIS MATTERS:", "").strip()
                current_context.append(context)
            elif current_question and line.strip():
                # Continuation of context
                current_context.append(line.strip())
        
        # Don't forget the last question
        if current_question:
            research_questions.append({
                "question": current_question,
                "context": " ".join(current_context).strip(),
                "source": ""
            })
    elif questions_json.exists():
        with open(questions_json, encoding="utf-8") as f:
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
