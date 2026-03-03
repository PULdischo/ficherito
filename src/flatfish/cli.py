"""Flatfish CLI - Command line interface using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from flatfish import __version__
from flatfish.config import (
    FlatfishConfig,
    get_default_config,
    load_config,
    load_env,
)

app = typer.Typer(
    name="flatfish",
    help="Historical document analysis CLI - Extract, analyze, and present handwritten text.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        rprint(f"[bold blue]flatfish[/bold blue] version {__version__}")
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
    """Flatfish - Historical document analysis CLI."""
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
    """Initialize a new Flatfish project."""
    path = path.resolve()
    path.mkdir(parents=True, exist_ok=True)

    config_path = path / "flatfish.yaml"
    env_path = path / ".env"
    env_example_path = path / ".env.example"

    # Check for existing files
    if not force:
        existing = []
        if config_path.exists():
            existing.append("flatfish.yaml")
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
    env_content = """# HuggingFace Access
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx

# DashScope API (for Qwen)
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx
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
    for dirname in ["transcriptions", "entities", "summaries"]:
        dirpath = path / dirname
        dirpath.mkdir(exist_ok=True)
        rprint(f"[green]✓[/green] Created {dirpath}/")

    rprint(
        Panel(
            "[bold]Project initialized![/bold]\n\n"
            "Next steps:\n"
            "1. Edit [cyan]flatfish.yaml[/cyan] with your dataset configuration\n"
            "2. Add your API keys to [cyan].env[/cyan]\n"
            "3. Run [cyan]flatfish validate[/cyan] to check your setup\n"
            "4. Run [cyan]flatfish process[/cyan] to start processing",
            title="🐟 Flatfish",
            border_style="blue",
        )
    )


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("flatfish.yaml"),
) -> None:
    """Validate configuration and API connections."""
    try:
        # Load and validate config
        rprint("[dim]Checking configuration...[/dim]")
        cfg = load_config(config)
        rprint("[green]✓[/green] Config file valid")

        # Load environment
        env = load_env()

        # Check HuggingFace token
        if env.huggingface_token:
            rprint("[green]✓[/green] HuggingFace token found")
            # TODO: Validate token by making API call
        else:
            rprint("[yellow]![/yellow] HuggingFace token not set (may be needed for private datasets)")

        # Check DashScope API key
        if cfg.summary.enabled:
            if env.dashscope_api_key:
                rprint("[green]✓[/green] DashScope API key found")
                # TODO: Validate key by making API call
            else:
                rprint("[red]✗[/red] DashScope API key not set (required for summary generation)")
                raise typer.Exit(1)

        # Check dataset accessibility
        rprint(f"[dim]Dataset: {cfg.dataset.source}[/dim]")
        # TODO: Try loading dataset to verify accessibility

        rprint("\n[bold green]Ready to process![/bold green]")

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
    ] = Path("flatfish.yaml"),
    split: Annotated[
        Optional[str],
        typer.Option("--split", "-s", help="Process only this split."),
    ] = None,
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
    skip_summary: Annotated[
        bool,
        typer.Option("--skip-summary", help="Skip summary generation."),
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
    from flatfish.pipeline import run_pipeline

    try:
        cfg = load_config(config)
        env = load_env()

        # Override splits if specified
        if split:
            cfg.dataset.splits = [split]

        run_pipeline(
            config=cfg,
            env=env,
            limit=limit,
            max_concurrent=concurrency,
            batch_size=batch_size,
            skip_entities=skip_entities or not cfg.processing.extract_entities,
            skip_summary=skip_summary or not cfg.summary.enabled,
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
    ] = Path("flatfish.yaml"),
    split: Annotated[
        Optional[str],
        typer.Option("--split", "-s", help="Process only this split."),
    ] = None,
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
    from flatfish.pipeline import run_extraction

    try:
        cfg = load_config(config)
        env = load_env()

        if split:
            cfg.dataset.splits = [split]

        run_extraction(config=cfg, env=env, limit=limit, max_concurrent=concurrency)

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def entities(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("flatfish.yaml"),
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
    from flatfish.pipeline import run_entity_extraction

    try:
        cfg = load_config(config)
        env = load_env()

        run_entity_extraction(config=cfg, env=env, limit=limit, max_concurrent=concurrency)

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def summarize(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("flatfish.yaml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force regeneration even if summary exists."),
    ] = False,
) -> None:
    """Generate AI summary from documents."""
    from flatfish.pipeline import run_summary

    try:
        cfg = load_config(config)
        env = load_env()

        run_summary(config=cfg, env=env, force=force)

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def combine(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("flatfish.yaml"),
) -> None:
    """Combine batch summaries into final summary.
    
    Use this after 'summarize' to merge batch files into the final summary.
    Useful when summarization is interrupted or combining failed previously.
    """
    from flatfish.summary.qwen import QwenSummarizer

    try:
        cfg = load_config(config)
        env = load_env()

        # Check for batch files - support both old and new directory structures
        summaries_dir = Path(cfg.output.summaries_dir)
        batches_dir = summaries_dir / "batches"
        
        if not batches_dir.exists():
            rprint(f"[yellow]No batch files found at {batches_dir}[/yellow]")
            raise typer.Exit(1)
        
        # Check for new track-based structure first
        track_dirs = ["timeline", "key_changes", "research_questions", "narrative"]
        has_track_dirs = any((batches_dir / track).exists() for track in track_dirs)
        
        if has_track_dirs:
            # New track-based structure
            total_batches = 0
            for track in track_dirs:
                track_dir = batches_dir / track
                if track_dir.exists():
                    count = len(list(track_dir.glob("batch_*.md")))
                    total_batches = max(total_batches, count)
                    rprint(f"[blue]  {track}: {count} batch files[/blue]")
            
            if total_batches == 0:
                rprint(f"[yellow]No batch files found in track directories[/yellow]")
                raise typer.Exit(1)
            
            rprint(f"[blue]Found {total_batches} batches across 4 tracks to combine[/blue]")
        else:
            # Old-style flat structure
            batch_files = sorted(batches_dir.glob("batch_*.md"))
            if not batch_files:
                rprint(f"[yellow]No batch files found in {batches_dir}[/yellow]")
                raise typer.Exit(1)
            
            rprint(f"[blue]Found {len(batch_files)} batch files to combine[/blue]")
        
        summarizer = QwenSummarizer(
            config=cfg,
            env=env,
        )
        
        # Run combine
        summary = summarizer.combine_batches(summaries_dir)
        
        # Save the combined summary
        summarizer.save_summary(summary, summaries_dir)
        rprint(f"[green]✓ Combined summary saved to {summaries_dir}[/green]")

    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def build(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config file."),
    ] = Path("flatfish.yaml"),
    output: Annotated[
        Optional[Path],
        typer.Option("--output", "-o", help="Output directory."),
    ] = None,
    base_url: Annotated[
        str,
        typer.Option("--base-url", help="Base URL for the site."),
    ] = "/",
) -> None:
    """Build static website with search indexing."""
    from flatfish.site.builder import build_site

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
    ] = Path("flatfish.yaml"),
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
                "Run 'flatfish build' first."
            )
            raise typer.Exit(1)

        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(site_dir))

        with socketserver.TCPServer((host, port), handler) as httpd:
            rprint(
                Panel(
                    f"Serving at [bold cyan]http://{host}:{port}[/bold cyan]\n"
                    "Press Ctrl+C to stop.",
                    title="🐟 Flatfish Preview Server",
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
    ] = Path("flatfish.yaml"),
) -> None:
    """Show processing status."""
    from rich.table import Table

    try:
        cfg = load_config(config)

        # Count files in each directory
        transcriptions_dir = Path(cfg.output.transcriptions_dir)
        entities_dir = Path(cfg.output.entities_dir)
        summaries_dir = Path(cfg.output.summaries_dir)
        site_dir = Path(cfg.output.site_dir)

        table = Table(title="Flatfish Status")
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

        # Summaries
        if summaries_dir.exists():
            has_summary = (summaries_dir / "full_summary.md").exists()
            table.add_row(
                "Summary",
                "[green]Complete[/green]" if has_summary else "[yellow]Not started[/yellow]",
                str(summaries_dir) if has_summary else "-",
            )
        else:
            table.add_row("Summary", "[yellow]Not started[/yellow]", "-")

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
    ] = Path("flatfish.yaml"),
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
                "Set netlify_site_id in flatfish.yaml, use --site flag, or set NETLIFY_SITE_ID env var.\n"
                "Find your site ID in the Netlify dashboard under Site Settings > General."
            )
            raise typer.Exit(1)

        # Build site first if requested
        if build_first:
            from flatfish.site.builder import build_site
            rprint("[dim]Building site...[/dim]")
            build_site(config=cfg, base_url="/")
            rprint(f"[green]✓[/green] Site built to {site_dir}/")

        # Check if site directory exists
        if not site_dir.exists():
            rprint(
                f"[red]Error:[/red] Site directory not found: {site_dir}\n"
                "Run 'flatfish build' first or use --build flag."
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
