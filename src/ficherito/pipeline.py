"""Pipeline orchestration for Ficherito processing."""

import asyncio
import json
from pathlib import Path
from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from ficherito.config import FicheritoConfig, EnvSettings
from ficherito.dataset import list_image_files, iter_document_images, save_image
from ficherito.htr.engine import HTREngine
from ficherito.entities.extractor import EntityExtractor, consolidate_entities, load_entities
from ficherito.site.builder import build_site
from ficherito.htr.engine import load_transcription
from ficherito.utils.console import get_console
from ficherito.utils.logging import setup_logging, get_logger

console = get_console()
logger = get_logger("pipeline")


def run_pipeline(
    config: FicheritoConfig,
    env: EnvSettings,
    limit: Optional[int] = None,
    max_concurrent: int = 10,
    batch_size: int = 50,
    skip_entities: bool = False,
    skip_build: bool = False,
    verbose: bool = False,
) -> None:
    """Run the complete processing pipeline.

    Args:
        config: Ficherito configuration.
        env: Environment settings.
        limit: Optional limit on documents to process.
        max_concurrent: Maximum concurrent API requests.
        batch_size: Number of images to process per batch.
        skip_entities: Skip entity extraction.
        skip_build: Skip site building.
        verbose: Enable verbose logging.
    """
    setup_logging(verbose=verbose)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        refresh_per_second=2,
    ) as progress:
        # Step 1: Extract text from images
        task = progress.add_task("Scanning images...", total=None)
        files = list_image_files(config)
        total = min(len(files), limit) if limit else len(files)
        progress.update(task, completed=True, total=1)

        # Step 2: Run HTR
        run_extraction(config, env, limit=limit, progress=progress, 
                       max_concurrent=max_concurrent, batch_size=batch_size)

        # Step 3: Extract entities
        if not skip_entities:
            run_entity_extraction(config, env, limit=limit, progress=progress, max_concurrent=max_concurrent)

        # Step 4: Build site
        if not skip_build:
            task = progress.add_task("Building website...", total=1)
            build_site(config)
            progress.update(task, completed=1)

    console.print("\n[bold green]✓ Pipeline complete![/bold green]")
    console.print(f"  Transcriptions: {config.output.transcriptions_dir}/")
    if not skip_entities:
        console.print(f"  Entities: {config.output.entities_dir}/")
    if not skip_build:
        console.print(f"  Website: {config.output.site_dir}/")


def run_extraction(
    config: FicheritoConfig,
    env: EnvSettings,
    limit: Optional[int] = None,
    progress: Optional[Progress] = None,
    max_concurrent: int = 10,
    batch_size: int = 50,
) -> None:
    """Run text extraction from images using async concurrent processing.

    Args:
        config: Ficherito configuration.
        env: Environment settings.
        limit: Optional limit on documents to process.
        progress: Optional progress bar.
        max_concurrent: Maximum concurrent API requests.
        batch_size: Number of images to process per batch (for memory efficiency).
    """
    # Scan local image folder
    files = list_image_files(config)
    total = min(len(files), limit) if limit else len(files)

    # Create output directories
    transcriptions_dir = Path(config.output.transcriptions_dir)
    transcriptions_dir.mkdir(parents=True, exist_ok=True)

    images_dir = Path("images")
    images_dir.mkdir(parents=True, exist_ok=True)

    # Initialize HTR engine with env for API key
    engine = HTREngine(config, env=env)

    task = None
    if progress:
        task = progress.add_task(f"Extracting text (0/{total})...", total=total)
    else:
        console.print(f"Extracting text from {total} images (async, {max_concurrent} concurrent)...")

    # Process in batches to avoid memory issues
    processed = [0]
    errors = [0]
    
    def on_complete(result):
        """Save result immediately as it completes."""
        try:
            engine.save_transcription(result, transcriptions_dir)
            processed[0] += 1
        except Exception as e:
            logger.error(f"Failed to save transcription {result.image_id}: {e}")
            errors[0] += 1
        
        if progress and task is not None:
            progress.advance(task)
            progress.update(task, description=f"Extracting text ({processed[0]}/{total})...")

    async def process_batch(batch_docs):
        """Process a batch of documents, saving results as they stream in."""
        await engine.extract_batch_async(
            batch_docs,
            max_concurrent=max_concurrent,
            on_complete=on_complete,
        )

    # Collect and process in batches, skipping already processed
    current_batch = []
    skipped = 0
    
    for doc in iter_document_images(config, limit=limit, files=files):
        # Check if transcription already exists
        transcript_path = transcriptions_dir / f"{doc.image_id}.md"
        if transcript_path.exists():
            skipped += 1
            if progress and task is not None:
                progress.advance(task)
                progress.update(task, description=f"Extracting text ({processed[0]}/{total}, {skipped} skipped)...")
            continue
        
        # Save image
        save_image(doc, images_dir)
        current_batch.append((doc.image, doc.image_id))
        
        # Process batch when full
        if len(current_batch) >= batch_size:
            asyncio.run(process_batch(current_batch))
            current_batch = []
    
    # Process remaining documents
    if current_batch:
        asyncio.run(process_batch(current_batch))
    
    if not progress:
        if skipped:
            console.print(f"[blue]ℹ[/blue] Skipped {skipped} images with existing transcriptions")
        console.print(f"[green]✓[/green] Extracted text from {processed[0]} images")
        if errors[0]:
            console.print(f"[yellow]![/yellow] {errors[0]} errors occurred")


def run_entity_extraction(
    config: FicheritoConfig,
    env: EnvSettings,
    limit: Optional[int] = None,
    progress: Optional[Progress] = None,
    max_concurrent: int = 10,
) -> None:
    """Run entity extraction from transcriptions using async concurrent processing.

    Args:
        config: Ficherito configuration.
        env: Environment settings.
        limit: Optional limit on documents to process.
        progress: Optional progress bar.
        max_concurrent: Maximum concurrent API requests.
    """
    transcriptions_dir = Path(config.output.transcriptions_dir)
    entities_dir = Path(config.output.entities_dir)
    entities_dir.mkdir(parents=True, exist_ok=True)

    # Get transcription files
    txt_files = list(transcriptions_dir.glob("*.md"))
    if limit:
        txt_files = txt_files[:limit]

    if not txt_files:
        console.print("[yellow]No transcriptions found. Run extraction first.[/yellow]")
        return

    # Initialize extractor
    extractor = EntityExtractor(config, env)

    # Filter out already processed files
    files_to_process = []
    skipped = 0
    for txt_file in txt_files:
        entity_path = entities_dir / f"{txt_file.stem}.json"
        if entity_path.exists():
            skipped += 1
        else:
            files_to_process.append(txt_file)

    task = None
    total = len(txt_files)
    if progress:
        task = progress.add_task(f"Extracting entities (0/{total})...", total=total)
        # Advance for skipped files
        for _ in range(skipped):
            progress.advance(task)
    else:
        if skipped:
            console.print(f"[blue]ℹ[/blue] Skipping {skipped} files with existing entities")
        console.print(f"Extracting entities from {len(files_to_process)} transcriptions (async, {max_concurrent} concurrent)...")

    if not files_to_process:
        if not progress:
            console.print("[green]✓[/green] All entities already extracted")
        return

    # Load documents that need processing
    documents = []
    for txt_file in files_to_process:
        try:
            text, _ = load_transcription(txt_file)
            documents.append({"id": txt_file.stem, "text": text})
        except Exception as e:
            logger.error(f"Failed to load {txt_file.name}: {e}")

    # Track results for consolidation
    all_results = []
    processed = [0]
    
    def on_complete(result):
        """Save entity result immediately as it completes."""
        try:
            extractor.save_entities(result, entities_dir)
            all_results.append(result)
            processed[0] += 1
        except Exception as e:
            logger.error(f"Failed to save entities for {result.source_image}: {e}")
        
        if progress and task is not None:
            progress.advance(task)
            progress.update(task, description=f"Extracting entities ({processed[0]}/{total})...")

    # Run async extraction with streaming results
    async def extract_all():
        await extractor.extract_batch_async(
            documents,
            max_concurrent=max_concurrent,
            on_complete=on_complete,
        )

    asyncio.run(extract_all())

    # Rebuild consolidated entities from ALL entity files (including previously extracted)
    all_entity_files = list(entities_dir.glob("*.json"))
    all_entity_files = [f for f in all_entity_files if f.name != "consolidated.json"]
    
    if all_entity_files:
        all_entity_results = []
        for entity_file in all_entity_files:
            try:
                result = load_entities(entity_file)
                all_entity_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to load {entity_file.name}: {e}")
        
        if all_entity_results:
            consolidated = consolidate_entities(all_entity_results)
            consolidated_path = entities_dir / "consolidated.json"
            with open(consolidated_path, "w", encoding="utf-8") as f:
                json.dump(consolidated, f, indent=2, ensure_ascii=False)

    if not progress:
        console.print(f"[green]✓[/green] Extracted entities from {len(all_results)} documents")
