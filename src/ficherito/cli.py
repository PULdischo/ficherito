"""Ficherito CLI - Command line interface using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml
from rich import print as rprint
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ficherito import __version__
from ficherito.utils.console import get_console
from ficherito.config import (
    FicheritoConfig,
    get_default_config,
    load_config,
    load_env,
)

app = typer.Typer(
    name="ficherito",
    help="Historical document analysis CLI - Extract, analyze, and present handwritten text.",
    add_completion=False,
)
console = get_console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        rprint(f"[bold blue]ficherito[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Ficherito - Historical document analysis CLI."""
    pass


@app.command()
def init(
    path: Annotated[
        Path,
        typer.Argument(help="Directory to initialize project in."),
    ] = Path("."),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing files."),
    ] = False,
) -> None:
    """Initialize a new Ficherito project."""
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)

    config_path = path / "ficherito.yaml"
    env_path = path / ".env"
    env_example_path = path / ".env.example"

    # Check for existing files
    if not force:
        existing = []
        if config_path.exists():
            existing.append("ficherito.yaml")
        if env_path.exists():
            existing.append(".env")
        if existing:
            rprint(
                f"[yellow]Warning:[/yellow] Files already exist: {', '.join(existing)}\n"
                "Use --force to overwrite."
            )
            raise typer.Exit(1)

    # Write config file
    default_config = get_default_config()
    with open(config_path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    rprint(f"[green]✓[/green] Created {config_path}")

    # Write .env.example
    env_content = """# OpenAI-compatible LLM endpoint (DashScope, OpenAI, local, etc.)
OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=qwen-vl-max
"""
    with open(env_example_path, "w") as f:
        f.write(env_content)
    rprint(f"[green]✓[/green] Created {env_example_path}")

    # Copy to .env if it doesn't exist
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_content)
        rprint(f"[green]✓[/green] Created {env_path}")

    # Create output directories
    for dirname in ["images", "transcriptions", "translations", "entities"]:
        dirpath = path / dirname
        dirpath.mkdir(exist_ok=True)
        rprint(f"[green]✓[/green] Created {dirpath}/")

    rprint(
        Panel(
            "[bold]Project initialized![/bold]\n\n"
            "Next steps:\n"
            "1. Edit [cyan]ficherito.yaml[/cyan] with your dataset configuration\n"
            "2. Add your API keys to [cyan].env[/cyan]\n"
            "3. Run [cyan]ficherito validate[/cyan] to check your setup\n"
            "4. Run [cyan]ficherito process[/cyan] to start processing",
            title="🐟 Ficherito",
            border_style="blue",
        )
    )


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
) -> None:
    """Validate configuration and API connections."""
    try:
        # Load and validate config
        rprint("[dim]Checking configuration...[/dim]")
        cfg = load_config(config)
        rprint("[green]✓[/green] Config file valid")

        # Load environment
        env = load_env()

        # Check LLM endpoint configuration
        if env.api_base_url:
            rprint(f"[green]✓[/green] LLM base URL: {env.api_base_url}")
        else:
            rprint("[yellow]![/yellow] OPENAI_BASE_URL not set (using provider default)")

        if env.api_key:
            rprint("[green]✓[/green] API key found")
        else:
            rprint("[red]✗[/red] OPENAI_API_KEY not set (required for extraction and summaries)")
            raise typer.Exit(1)

        if env.api_model:
            rprint(f"[green]✓[/green] Model: {env.api_model}")
        else:
            rprint("[yellow]![/yellow] OPENAI_MODEL not set (using built-in default)")

        # Check images folder
        images_dir = Path(cfg.dataset.images_dir)
        if images_dir.exists():
            rprint(f"[green]✓[/green] Images folder: {images_dir}")
        else:
            rprint(f"[yellow]![/yellow] Images folder not found: {images_dir}")

        # Live API check: run one real extraction on a random image so a bad
        # base URL / key / model is caught here instead of during `process`.
        if env.api_key and images_dir.exists():
            import random

            from PIL import Image

            from ficherito.dataset import list_image_files
            from ficherito.htr.engine import HTREngine

            try:
                image_files = list_image_files(cfg)
            except FileNotFoundError:
                image_files = []

            if not image_files:
                rprint("[yellow]![/yellow] No images found to test extraction")
            else:
                sample = random.choice(image_files)
                rprint(f"[dim]Testing extraction on {sample.name}...[/dim]")
                try:
                    with Image.open(sample) as im:
                        text = HTREngine(cfg, env).test_connection(im)
                except Exception as e:
                    rprint(f"[red]✗[/red] Extraction test failed: {e}")
                    rprint(
                        "[dim]Check OPENAI_BASE_URL, OPENAI_API_KEY and "
                        "OPENAI_MODEL in .env[/dim]"
                    )
                    raise typer.Exit(1)

                preview = " ".join(text.split())[:60]
                rprint(
                    f"[green]✓[/green] Extraction test passed "
                    f'([dim]"{preview}…"[/dim])'
                )

        rprint("\n[bold green]Ready to process![/bold green]")

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def process(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", "-l", help="Limit number of documents to process."),
    ] = None,
    concurrency: Annotated[
        int,
        typer.Option("--concurrency", "-j", help="Number of concurrent API requests."),
    ] = 10,
    batch_size: Annotated[
        int,
        typer.Option("--batch-size", "-b", help="Images per batch (for memory efficiency)."),
    ] = 50,
    skip_entities: Annotated[
        bool,
        typer.Option("--skip-entities", help="Skip entity extraction."),
    ] = False,
    skip_build: Annotated[
        bool,
        typer.Option("--skip-build", help="Skip site building."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Verbose output."),
    ] = False,
) -> None:
    """Run the full processing pipeline."""
    from ficherito.pipeline import run_pipeline

    try:
        cfg = load_config(config)
        env = load_env()

        run_pipeline(
            config=cfg,
            env=env,
            limit=limit,
            max_concurrent=concurrency,
            batch_size=batch_size,
            skip_entities=skip_entities or not cfg.processing.extract_entities,
            skip_build=skip_build,
            verbose=verbose,
        )

    except FileNotFoundError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def extract(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", "-l", help="Limit number of documents."),
    ] = None,
    concurrency: Annotated[
        int,
        typer.Option("--concurrency", "-j", help="Number of concurrent API requests."),
    ] = 10,
) -> None:
    """Extract text from images only."""
    from ficherito.pipeline import run_extraction

    try:
        cfg = load_config(config)
        env = load_env()

        run_extraction(config=cfg, env=env, limit=limit, max_concurrent=concurrency)

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def entities(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", "-l", help="Limit number of documents."),
    ] = None,
    concurrency: Annotated[
        int,
        typer.Option("--concurrency", "-j", help="Number of concurrent API requests."),
    ] = 10,
) -> None:
    """Extract entities from transcriptions."""
    from ficherito.pipeline import run_entity_extraction

    try:
        cfg = load_config(config)
        env = load_env()

        run_entity_extraction(config=cfg, env=env, limit=limit, max_concurrent=concurrency)

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def translate(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    limit: Annotated[
        Optional[int],
        typer.Option("--limit", "-l", help="Limit number of documents to translate."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force re-translation even if translation exists."),
    ] = False,
    source_language: Annotated[
        Optional[str],
        typer.Option("--source", "-s", help="Override source language (default: from config or 'auto')."),
    ] = None,
) -> None:
    """Translate transcriptions to target language.
    
    Uses Google Translate via deep_translator. Validates language codes
    against supported languages before running.
    """
    from ficherito.translation import Translator, validate_languages
    from ficherito.htr.engine import load_transcription

    try:
        cfg = load_config(config)
        
        if not cfg.translate.enabled:
            rprint("[yellow]Translation is disabled in config. Enable it with translate.enabled: true[/yellow]")
            raise typer.Exit(1)
        
        # Validate languages
        source_langs = [source_language] if source_language else cfg.translate.source_languages
        is_valid, error = validate_languages(source_langs, cfg.translate.target_language)
        
        if not is_valid:
            rprint(f"[red]Error:[/red] {error}")
            raise typer.Exit(1)
        
        rprint(f"[blue]Translating from {source_langs} to {cfg.translate.target_language}[/blue]")
        
        # Initialize translator
        translator = Translator(config=cfg)
        
        # Load transcriptions
        transcriptions_dir = Path(cfg.output.transcriptions_dir)
        translations_dir = Path(cfg.output.translations_dir)
        translations_dir.mkdir(parents=True, exist_ok=True)
        
        if not transcriptions_dir.exists():
            rprint(f"[red]Error:[/red] Transcriptions directory not found: {transcriptions_dir}")
            raise typer.Exit(1)
        
        transcription_files = sorted(transcriptions_dir.glob("*.md"))
        if limit:
            transcription_files = transcription_files[:limit]
        
        total = len(transcription_files)
        translated = 0
        skipped = 0
        errors = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Translating 0/{total}...", total=total)
            
            for txt_file in transcription_files:
                doc_id = txt_file.stem
                output_file = translations_dir / f"{doc_id}.md"
                
                # Skip if already translated (unless force)
                if output_file.exists() and not force:
                    skipped += 1
                    progress.advance(task)
                    progress.update(task, description=f"Translating {translated}/{total} (skipped {skipped})...")
                    continue
                
                # Load transcription
                text, _ = load_transcription(txt_file)
                
                # Translate
                src_lang = source_language or cfg.translate.source_languages[0]
                result = translator.translate_document(doc_id, text, src_lang)
                
                if result.success:
                    translator.save_translation(result, translations_dir)
                    translated += 1
                else:
                    errors += 1
                    rprint(f"[red]Error translating {doc_id}: {result.error}[/red]")
                
                progress.advance(task)
                progress.update(task, description=f"Translating {translated}/{total} (skipped {skipped})...")
        
        rprint(f"\n[green]✓[/green] Translation complete!")
        rprint(f"  Translated: {translated}")
        rprint(f"  Skipped: {skipped}")
        if errors:
            rprint(f"  [red]Errors: {errors}[/red]")

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def build(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory."),
    ] = None,
    base_url: Annotated[
        str,
        typer.Option("--base-url", help="Path prefix the site is served under (e.g. '/my-repo/' for GitHub Pages project sites)."),
    ] = "/",
) -> None:
    """Build static website with search indexing."""
    from ficherito.site.builder import build_site

    try:
        cfg = load_config(config)

        if output:
            cfg.output.site_dir = str(output)

        build_site(
            config=cfg,
            base_url=base_url,
        )

        rprint(f"[green]✓[/green] Site built to {cfg.output.site_dir}/")

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to serve on."),
    ] = 8000,
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Host to bind to."),
    ] = "localhost",
) -> None:
    """Serve the built site locally for preview."""
    import http.server
    import socketserver
    from functools import partial

    try:
        cfg = load_config(config)
        site_dir = Path(cfg.output.site_dir)

        if not site_dir.exists():
            rprint(
                f"[red]Error:[/red] Site directory not found: {site_dir}\n"
                "Run 'ficherito build' first."
            )
            raise typer.Exit(1)

        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(site_dir))

        with socketserver.TCPServer((host, port), handler) as httpd:
            rprint(
                Panel(
                    f"Serving at [bold cyan]http://{host}:{port}[/bold cyan]\n"
                    "Press Ctrl+C to stop.",
                    title="🐟 Ficherito Preview Server",
                    border_style="blue",
                )
            )
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                rprint("\n[dim]Server stopped.[/dim]")

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def status(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
) -> None:
    """Show processing status."""
    from rich.table import Table

    try:
        cfg = load_config(config)

        # Count files in each directory
        transcriptions_dir = Path(cfg.output.transcriptions_dir)
        entities_dir = Path(cfg.output.entities_dir)
        site_dir = Path(cfg.output.site_dir)

        table = Table(title="Ficherito Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        # Transcriptions
        if transcriptions_dir.exists():
            count = len(list(transcriptions_dir.glob("*.md")))
            table.add_row("Transcriptions", f"{count} files", str(transcriptions_dir))
        else:
            table.add_row("Transcriptions", "[yellow]Not started[/yellow]", "-")

        # Entities
        if entities_dir.exists():
            count = len(list(entities_dir.glob("*.json")))
            table.add_row("Entities", f"{count} files", str(entities_dir))
        else:
            table.add_row("Entities", "[yellow]Not started[/yellow]", "-")

        # Site
        if site_dir.exists():
            has_index = (site_dir / "index.html").exists()
            table.add_row(
                "Website",
                "[green]Built[/green]" if has_index else "[yellow]Incomplete[/yellow]",
                str(site_dir),
            )
        else:
            table.add_row("Website", "[yellow]Not built[/yellow]", "-")

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def deploy(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("ficherito.yaml"),
    prod: Annotated[
        bool,
        typer.Option("--prod/--draft", help="Deploy to production (default) or draft preview."),
    ] = True,
    site: Annotated[
        Optional[str],
        typer.Option("--site", "-s", help="Netlify site ID (required)."),
    ] = None,
    build_first: Annotated[
        bool,
        typer.Option("--build/--no-build", help="Build site before deploying."),
    ] = True,
) -> None:
    """Deploy site to Netlify using netlify-python.
    
    Requires NETLIFY_TOKEN in .env file or environment.
    Get a token from: https://app.netlify.com/user/applications#personal-access-tokens
    """
    import zipfile
    import tempfile
    import os
    from dotenv import load_dotenv

    # Load .env file
    load_dotenv()

    try:
        from netlify import NetlifyClient
    except ImportError:
        rprint(
            "[red]Error:[/red] netlify-python not installed.\n"
            "Install it with: [cyan]pip install netlify-python[/cyan]"
        )
        raise typer.Exit(1)

    try:
        cfg = load_config(config)
        site_dir = Path(cfg.output.site_dir)

        # Check for Netlify token
        token = os.environ.get("NETLIFY_TOKEN")
        if not token:
            rprint(
                "[red]Error:[/red] NETLIFY_TOKEN not found.\n"
                "Add it to your .env file: [cyan]NETLIFY_TOKEN=your-token[/cyan]\n"
                "Get a token from: [cyan]https://app.netlify.com/user/applications#personal-access-tokens[/cyan]"
            )
            raise typer.Exit(1)

        # Check for site ID (CLI flag > config > env var)
        site_id = site or cfg.website.netlify_site_id or os.environ.get("NETLIFY_SITE_ID")
        if not site_id:
            rprint(
                "[red]Error:[/red] No site ID provided.\n"
                "Set netlify_site_id in ficherito.yaml, use --site flag, or set NETLIFY_SITE_ID env var.\n"
                "Find your site ID in the Netlify dashboard under Site Settings > General."
            )
            raise typer.Exit(1)

        # Build site first if requested
        if build_first:
            from ficherito.site.builder import build_site
            rprint("[dim]Building site...[/dim]")
            build_site(config=cfg, base_url="/")
            rprint(f"[green]✓[/green] Site built to {site_dir}/")

        # Check if site directory exists
        if not site_dir.exists():
            rprint(
                f"[red]Error:[/red] Site directory not found: {site_dir}\n"
                "Run 'ficherito build' first or use --build flag."
            )
            raise typer.Exit(1)

        # Create zip file of site
        rprint("[dim]Creating deployment package...[/dim]")
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in site_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(site_dir)
                    zipf.write(file_path, arcname)

        deploy_type = "production" if prod else "draft"
        rprint(f"[dim]Deploying to Netlify ({deploy_type})...[/dim]")

        # Deploy using netlify-python
        client = NetlifyClient(access_token=token)
        
        # Note: netlify-python's create_site_deploy handles both draft and prod
        deploy = client.create_site_deploy(site_id, zip_path)
        
        # Clean up zip file
        os.unlink(zip_path)

        # Get deploy URL
        deploy_url = getattr(deploy, 'deploy_ssl_url', None) or getattr(deploy, 'deploy_url', None) or getattr(deploy, 'ssl_url', 'Netlify')
        
        rprint(f"[green]✓[/green] Site deployed to Netlify ({deploy_type})")
        rprint(f"[cyan]URL:[/cyan] {deploy_url}")

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
