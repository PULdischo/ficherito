"""Static site builder for Flatfish."""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import markdown
from jinja2 import Environment, PackageLoader, select_autoescape

from flatfish.config import FlatfishConfig
from flatfish.entities.extractor import load_entities, consolidate_entities, EntityExtractionResult
from flatfish.htr.engine import load_transcription
from flatfish.summary.qwen import load_summary, DocumentSummary
from flatfish.utils.dates import sort_by_date, format_date_display, extract_date_from_filename
from flatfish.utils.logging import get_logger

logger = get_logger("site.builder")


@dataclass
class DocumentData:
    """Data for a single document page."""

    id: str
    filename: str
    date: Optional[str]
    date_display: str
    transcription: str
    entities: list[dict]
    image_path: str
    prev_doc: Optional[str] = None
    next_doc: Optional[str] = None


class SiteBuilder:
    """Builds static website from processed documents."""

    def __init__(
        self,
        config: FlatfishConfig,
        base_url: str = "/",
    ):
        """Initialize the site builder.

        Args:
            config: Flatfish configuration.
            base_url: Base URL for the site.
        """
        self.config = config
        self.base_url = base_url.rstrip("/")

        # Set up Jinja2 environment
        self.env = Environment(
            loader=PackageLoader("flatfish", "site/templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Add custom filters
        self.env.filters["format_date"] = format_date_display

    def build(
        self,
        enable_search: bool = True,
    ) -> Path:
        """Build the complete static site.

        Args:
            enable_search: Whether to run Pagefind indexing.

        Returns:
            Path to built site.
        """
        output_dir = Path(self.config.output.site_dir)

        # Clean output directory
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

        # Load all data
        documents = self._load_documents()
        summary = self._load_summary()
        consolidated_entities = self._load_consolidated_entities()

        # Sort documents by date
        documents = sort_by_date(documents, date_key="date")

        # Add prev/next links
        for i, doc in enumerate(documents):
            if i > 0:
                doc["prev_doc"] = documents[i - 1]["id"]
            if i < len(documents) - 1:
                doc["next_doc"] = documents[i + 1]["id"]

        # Build pages
        self._build_index_page(output_dir)
        self._build_main_page(output_dir, documents, summary, consolidated_entities)
        self._build_overview_page(output_dir, summary)
        self._build_document_pages(output_dir, documents, summary)
        self._build_browse_pages(output_dir, documents, consolidated_entities, summary)

        # Copy assets
        self._copy_assets(output_dir)

        # Copy images
        self._copy_images(output_dir, documents)

        # Run Pagefind if enabled
        if enable_search:
            self._run_pagefind(output_dir)

        logger.info(f"Site built to {output_dir}")
        return output_dir

    def _load_documents(self) -> list[dict]:
        """Load all processed documents."""
        documents = []
        transcriptions_dir = Path(self.config.output.transcriptions_dir)
        entities_dir = Path(self.config.output.entities_dir)

        if not transcriptions_dir.exists():
            return documents

        for txt_file in sorted(transcriptions_dir.glob("*.md")):
            doc_id = txt_file.stem

            # Load transcription
            text, metadata = load_transcription(txt_file)

            # Load entities if available
            entities = []
            entity_file = entities_dir / f"{doc_id}.json"
            if entity_file.exists():
                result = load_entities(entity_file)
                entities = [
                    {
                        "text": e.text,
                        "type": e.type,
                        "context": e.context,
                    }
                    for e in result.entities
                ]

            # Extract date from filename
            date = extract_date_from_filename(doc_id)

            # Convert markdown to HTML
            transcription_html = markdown.markdown(text, extensions=['nl2br', 'sane_lists'])

            documents.append({
                "id": doc_id,
                "filename": f"{doc_id}.jpg",
                "date": date,
                "date_display": format_date_display(date),
                "transcription": transcription_html,
                "entities": entities,
                "metadata": metadata,
            })

        return documents

    def _load_summary(self) -> Optional[dict]:
        """Load summary if available."""
        summaries_dir = Path(self.config.output.summaries_dir)
        if not (summaries_dir / "full_summary.md").exists():
            return None

        try:
            summary = load_summary(summaries_dir)
            # Convert full_text markdown to HTML
            return {
                "timeline": summary.timeline,
                "key_changes": summary.key_changes,
                "research_questions": summary.research_questions,
                "full_text": markdown.markdown(summary.full_text, extensions=['tables', 'sane_lists']),
                "generated_at": summary.generated_at,
                "model": summary.model,
                "document_count": summary.document_count,
            }
        except Exception as e:
            logger.warning(f"Failed to load summary: {e}")
            return None

    def _load_consolidated_entities(self) -> dict:
        """Load consolidated entities."""
        entities_dir = Path(self.config.output.entities_dir)
        consolidated_path = entities_dir / "consolidated.json"

        if consolidated_path.exists():
            with open(consolidated_path, encoding="utf-8") as f:
                return json.load(f)

        # Generate on the fly if not exists
        results = []
        for entity_file in entities_dir.glob("*.json"):
            if entity_file.name != "consolidated.json":
                try:
                    results.append(load_entities(entity_file))
                except Exception:
                    pass

        if results:
            return consolidate_entities(results)

        return {"by_type": {}, "all_entities": []}

    def _build_index_page(self, output_dir: Path) -> None:
        """Build password-protected index page."""
        template = self.env.get_template("index.html")

        html = template.render(
            title=self.config.website.title,
            emoji=self.config.website.emoji,
            background_color=self.config.website.background_color,
            accent_color=self.config.website.accent_color,
            password=self.config.website.password,
            base_url=self.base_url,
        )

        with open(output_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)

    def _build_main_page(
        self,
        output_dir: Path,
        documents: list[dict],
        summary: Optional[DocumentSummary],
        consolidated_entities: dict,
    ) -> None:
        """Build main browse/search page."""
        template = self.env.get_template("main.html")

        html = template.render(
            title=self.config.website.title,
            emoji=self.config.website.emoji,
            background_color=self.config.website.background_color,
            accent_color=self.config.website.accent_color,
            documents=documents,
            summary=summary,
            entities=consolidated_entities,
            enable_search=self.config.website.enable_search,
            enable_browse_dates=self.config.website.enable_browse_dates,
            enable_browse_entities=self.config.website.enable_browse_entities,
            default_sort=self.config.website.default_sort,
            base_url=self.base_url,
        )

        with open(output_dir / "main.html", "w", encoding="utf-8") as f:
            f.write(html)

    def _build_overview_page(self, output_dir: Path, summary: Optional[dict]) -> None:
        """Build collection overview pages (summary, timeline, changes, questions)."""
        if not summary:
            return

        # Create overview directory
        overview_dir = output_dir / "overview"
        overview_dir.mkdir(exist_ok=True)

        # Common template context
        context = {
            "title": self.config.website.title,
            "emoji": self.config.website.emoji,
            "background_color": self.config.website.background_color,
            "accent_color": self.config.website.accent_color,
            "summary": summary,
            "enable_browse_dates": self.config.website.enable_browse_dates,
            "enable_browse_entities": self.config.website.enable_browse_entities,
            "base_url": self.base_url,
        }

        # Build each overview page
        overview_pages = [
            ("overview/summary.html", "summary.html"),
            ("overview/timeline.html", "timeline.html"),
            ("overview/changes.html", "changes.html"),
            ("overview/questions.html", "questions.html"),
        ]

        for template_path, output_name in overview_pages:
            template = self.env.get_template(template_path)
            html = template.render(**context)
            with open(overview_dir / output_name, "w", encoding="utf-8") as f:
                f.write(html)

        # Also build redirect page at old location
        redirect_template = self.env.get_template("overview.html")
        redirect_html = redirect_template.render(**context)
        with open(output_dir / "overview.html", "w", encoding="utf-8") as f:
            f.write(redirect_html)

    def _build_document_pages(self, output_dir: Path, documents: list[dict], summary: Optional[dict] = None) -> None:
        """Build individual document pages."""
        template = self.env.get_template("document.html")
        docs_dir = output_dir / "documents"
        docs_dir.mkdir(exist_ok=True)

        for doc in documents:
            doc_dir = docs_dir / doc["id"]
            doc_dir.mkdir(exist_ok=True)

            html = template.render(
                title=self.config.website.title,
                emoji=self.config.website.emoji,
                background_color=self.config.website.background_color,
                accent_color=self.config.website.accent_color,
                document=doc,
                base_url=self.base_url,
                summary=summary,
                enable_browse_dates=self.config.website.enable_browse_dates,
                enable_browse_entities=self.config.website.enable_browse_entities,
            )

            with open(doc_dir / "index.html", "w", encoding="utf-8") as f:
                f.write(html)

    def _build_browse_pages(
        self,
        output_dir: Path,
        documents: list[dict],
        consolidated_entities: dict,
        summary: Optional[dict] = None,
    ) -> None:
        """Build browse by dates and entities pages."""
        browse_dir = output_dir / "browse"
        browse_dir.mkdir(exist_ok=True)

        # Browse by dates
        if self.config.website.enable_browse_dates:
            template = self.env.get_template("browse_dates.html")

            # Group documents by date
            by_date: dict[str, list] = {}
            for doc in documents:
                date = doc.get("date") or "Unknown"
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append(doc)

            html = template.render(
                title=self.config.website.title,
                emoji=self.config.website.emoji,
                background_color=self.config.website.background_color,
                accent_color=self.config.website.accent_color,
                documents_by_date=by_date,
                base_url=self.base_url,
                summary=summary,
            )

            with open(browse_dir / "dates.html", "w", encoding="utf-8") as f:
                f.write(html)

        # Browse by entities
        if self.config.website.enable_browse_entities:
            template = self.env.get_template("browse_entities.html")

            html = template.render(
                title=self.config.website.title,
                emoji=self.config.website.emoji,
                background_color=self.config.website.background_color,
                accent_color=self.config.website.accent_color,
                entities=consolidated_entities,
                base_url=self.base_url,
                summary=summary,
            )

            with open(browse_dir / "entities.html", "w", encoding="utf-8") as f:
                f.write(html)

    def _copy_assets(self, output_dir: Path) -> None:
        """Copy static assets to output directory."""
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Copy CSS
        css_dir = assets_dir / "css"
        css_dir.mkdir(exist_ok=True)

        # Create main CSS file
        css_content = self._generate_css()
        with open(css_dir / "style.css", "w", encoding="utf-8") as f:
            f.write(css_content)

        # Copy JS
        js_dir = assets_dir / "js"
        js_dir.mkdir(exist_ok=True)

        # Create main JS file
        js_content = self._generate_js()
        with open(js_dir / "main.js", "w", encoding="utf-8") as f:
            f.write(js_content)

    def _copy_images(self, output_dir: Path, documents: list[dict]) -> None:
        """Copy document images to output directory."""
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Look for images in common locations
        possible_dirs = [
            Path("images"),
            Path("data/images"),
            Path(self.config.output.transcriptions_dir).parent / "images",
        ]

        for doc in documents:
            for src_dir in possible_dirs:
                for ext in [".jpg", ".jpeg", ".png", ".tiff", ".webp"]:
                    src_path = src_dir / f"{doc['id']}{ext}"
                    if src_path.exists():
                        dst_path = images_dir / f"{doc['id']}{ext}"
                        shutil.copy2(src_path, dst_path)
                        break

    def _run_pagefind(self, output_dir: Path) -> None:
        """Run Pagefind to index the site."""
        try:
            result = subprocess.run(
                ["npx", "pagefind", "--source", str(output_dir), "--bundle-dir", "pagefind"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("Pagefind indexing complete")
            else:
                logger.warning(f"Pagefind failed: {result.stderr}")
        except FileNotFoundError:
            logger.warning("Pagefind not found. Install with: npm install -g pagefind")

    def _generate_css(self) -> str:
        """Generate the main CSS file."""
        return """/* Flatfish - Document Collection Styles */

:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --background-color: #f8fafc;
    --text-color: #1e293b;
    --border-color: #e2e8f0;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

/* Header */
header {
    background: white;
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
    text-decoration: none;
}

nav a {
    margin-left: 1.5rem;
    color: var(--secondary-color);
    text-decoration: none;
}

nav a:hover {
    color: var(--primary-color);
}

nav a.active {
    color: var(--primary-color);
    font-weight: 600;
}

/* Dropdown menu */
.dropdown {
    position: relative;
    display: inline-block;
    margin-left: 1.5rem;
}

.dropdown-toggle {
    color: var(--secondary-color);
    text-decoration: none;
    cursor: pointer;
    background: none;
    border: none;
    font-size: inherit;
    font-family: inherit;
    padding: 0;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.dropdown-toggle:hover {
    color: var(--primary-color);
}

.dropdown-toggle.active {
    color: var(--primary-color);
    font-weight: 600;
}

.dropdown-toggle::after {
    content: '▾';
    font-size: 0.75rem;
}

.dropdown-menu {
    position: absolute;
    top: 100%;
    left: 0;
    min-width: 200px;
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 0.5rem 0;
    display: none;
    z-index: 1000;
}

.dropdown:hover .dropdown-menu,
.dropdown.open .dropdown-menu {
    display: block;
}

.dropdown-menu a {
    display: block;
    padding: 0.5rem 1rem;
    color: var(--text-color);
    text-decoration: none;
    margin: 0;
}

.dropdown-menu a:hover {
    background: var(--background-color);
    color: var(--primary-color);
}

.dropdown-menu a.active {
    color: var(--primary-color);
    font-weight: 600;
}

/* Search */
.search-container {
    padding: 2rem 0;
}

#search {
    max-width: 80%;
    margin: 0 auto;
}

/* Sort controls */
.sort-controls {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    align-items: center;
}

.sort-controls label {
    font-weight: 500;
}

.sort-controls button {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    background: white;
    border-radius: 4px;
    cursor: pointer;
}

.sort-controls button.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

/* Document grid */
.document-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
    padding: 2rem 0;
}

.document-card {
    background: white;
    border-radius: 8px;
    box-shadow: var(--card-shadow);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}

.document-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.document-card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.document-card-content {
    padding: 1rem;
}

.document-card h3 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
}

.document-card .date {
    color: var(--secondary-color);
    font-size: 0.875rem;
}

/* Document viewer */
.document-viewer {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    padding: 2rem 0;
    min-height: calc(100vh - 200px);
}

@media (max-width: 768px) {
    .document-viewer {
        grid-template-columns: 1fr;
    }
}

.image-viewer {
    background: #1e293b;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    min-height: calc(100vh - 250px);
}

#openseadragon {
    width: 100%;
    height: calc(100vh - 250px);
}

.document-content {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: var(--card-shadow);
}

.transcription {
    white-space: pre-wrap;
    font-family: Georgia, serif;
    line-height: 1.8;
    margin-bottom: 2rem;
}

.entities-list h3 {
    margin-bottom: 1rem;
    color: var(--secondary-color);
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.entity {
    display: flex;
    align-items: flex-start;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: var(--background-color);
    border-radius: 4px;
}

.entity-icon {
    margin-right: 0.75rem;
    font-size: 1.25rem;
}

.entity-text {
    font-weight: 500;
}

.entity-context {
    font-size: 0.875rem;
    color: var(--secondary-color);
}

/* Browse pages */
.browse-section {
    padding: 2rem 0;
}

.browse-section h2 {
    margin-bottom: 1.5rem;
}

.date-group {
    margin-bottom: 2rem;
}

.date-group h3 {
    color: var(--primary-color);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary-color);
}

.entity-type-group {
    margin-bottom: 2rem;
}

.entity-type-group h3 {
    text-transform: uppercase;
    font-size: 0.875rem;
    color: var(--secondary-color);
    margin-bottom: 1rem;
}

/* Summary section */
.summary-section {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: var(--card-shadow);
}

.summary-section h2 {
    margin-bottom: 1.5rem;
}

.summary-section h3 {
    margin-bottom: 1rem;
    color: var(--text-color);
    font-size: 1.1rem;
}

.summary-overview {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border-color);
}

.summary-text {
    font-family: Georgia, serif;
    line-height: 1.8;
    margin-bottom: 1rem;
}

.summary-text p {
    margin-bottom: 1rem;
}

.summary-text h1, .summary-text h2, .summary-text h3 {
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

.summary-meta {
    color: var(--secondary-color);
    font-size: 0.875rem;
}

.timeline {
    margin-bottom: 2rem;
}

.timeline-item {
    display: flex;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border-color);
}

.timeline-date {
    font-weight: 600;
    min-width: 120px;
    color: var(--primary-color);
}

.key-changes {
    margin-bottom: 2rem;
}

.change-item {
    display: flex;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border-color);
}

.change-type {
    font-weight: 600;
    min-width: 120px;
    color: #7c3aed;
    text-transform: capitalize;
}

.change-description {
    flex: 1;
}

.research-questions {
    margin-bottom: 1rem;
}

.research-questions li {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-color);
}

/* Password page */
.password-page {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
}

.password-form {
    background: white;
    padding: 3rem;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    text-align: center;
    max-width: 400px;
    width: 90%;
}

.password-form h1 {
    margin-bottom: 0.5rem;
    color: var(--text-color);
}

.password-form p {
    color: var(--secondary-color);
    margin-bottom: 2rem;
}

.password-form input {
    width: 100%;
    padding: 1rem;
    font-size: 1rem;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    margin-bottom: 1rem;
}

.password-form input:focus {
    outline: none;
    border-color: var(--primary-color);
}

.password-form button {
    width: 100%;
    padding: 1rem;
    font-size: 1rem;
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
}

.password-form button:hover {
    background: #1d4ed8;
}

.password-error {
    color: #dc2626;
    margin-top: 1rem;
    display: none;
}

/* Navigation */
.doc-navigation {
    display: flex;
    justify-content: space-between;
    padding: 1rem 0;
    border-top: 1px solid var(--border-color);
    margin-top: 2rem;
}

.doc-navigation a {
    color: var(--primary-color);
    text-decoration: none;
}

.doc-navigation a:hover {
    text-decoration: underline;
}

/* Footer */
footer {
    background: white;
    border-top: 1px solid var(--border-color);
    padding: 2rem 0;
    margin-top: 4rem;
    text-align: center;
    color: var(--secondary-color);
}
"""

    def _generate_js(self) -> str:
        """Generate the main JavaScript file."""
        return """/* Flatfish - Document Collection Scripts */

// Auth check
function checkAuth() {
    const auth = sessionStorage.getItem('flatfish_auth');
    if (!auth && !window.location.pathname.endsWith('index.html') && window.location.pathname !== '/') {
        window.location.href = 'index.html';
    }
}

// Password handling
function handlePassword(event) {
    event.preventDefault();
    const password = document.getElementById('password').value;
    const correctPassword = document.getElementById('password-form').dataset.password;
    
    if (password === correctPassword) {
        sessionStorage.setItem('flatfish_auth', 'true');
        window.location.href = 'main.html';
    } else {
        document.getElementById('password-error').style.display = 'block';
    }
}

// Sorting
function sortDocuments(sortBy) {
    const grid = document.querySelector('.document-grid');
    if (!grid) return;
    
    const cards = Array.from(grid.querySelectorAll('.document-card'));
    
    cards.sort((a, b) => {
        if (sortBy === 'date') {
            const dateA = a.dataset.date || 'z';
            const dateB = b.dataset.date || 'z';
            return dateA.localeCompare(dateB);
        } else if (sortBy === 'name') {
            const nameA = a.dataset.name || '';
            const nameB = b.dataset.name || '';
            return nameA.localeCompare(nameB);
        }
        return 0;
    });
    
    cards.forEach(card => grid.appendChild(card));
    
    // Update active button
    document.querySelectorAll('.sort-controls button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.sort === sortBy);
    });
}

// Initialize OpenSeaDragon
function initViewer(imageUrl) {
    if (typeof OpenSeadragon === 'undefined') {
        console.error('OpenSeadragon not loaded');
        return;
    }
    
    const viewer = OpenSeadragon({
        id: 'openseadragon',
        prefixUrl: 'https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/',
        tileSources: {
            type: 'image',
            url: imageUrl
        },
        showNavigator: true,
        navigatorPosition: 'BOTTOM_RIGHT',
        minZoomLevel: 0.5,
        maxZoomLevel: 10,
        visibilityRatio: 0.5,
        constrainDuringPan: true,
    });
    
    return viewer;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check auth on protected pages
    if (!document.querySelector('.password-page')) {
        checkAuth();
    }
    
    // Initialize sorting
    const defaultSort = document.body.dataset.defaultSort || 'date';
    sortDocuments(defaultSort);
    
    // Initialize OpenSeaDragon if present
    const viewerElement = document.getElementById('openseadragon');
    if (viewerElement) {
        const imageUrl = viewerElement.dataset.image;
        if (imageUrl) {
            initViewer(imageUrl);
        }
    }
});
"""


def build_site(
    config: FlatfishConfig,
    base_url: str = "/",
    enable_search: bool = True,
) -> Path:
    """Build the static site.

    Args:
        config: Flatfish configuration.
        base_url: Base URL for the site.
        enable_search: Whether to enable Pagefind search.

    Returns:
        Path to built site.
    """
    builder = SiteBuilder(config, base_url)
    return builder.build(enable_search=enable_search)
