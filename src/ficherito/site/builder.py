"""Site builder for Ficherito.

Emits Markdown + frontmatter + images into an Eleventy (11ty) project's
content directory, then runs Eleventy (and Pagefind, via its own
``eleventy.after`` hook) to produce the final static site.
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import yaml
from PIL import Image

from ficherito.config import FicheritoConfig
from ficherito.entities.extractor import load_entities, consolidate_entities
from ficherito.htr.engine import load_transcription
from ficherito.utils.dates import (
    sort_by_date,
    format_date_display,
    extract_date_from_filename,
    extract_full_date_from_text,
    infer_document_date,
)
from ficherito.utils.logging import get_logger

logger = get_logger("site.builder")

SCAFFOLD_DIR = Path(__file__).parent / "scaffold"

# Image compression settings
MAX_IMAGE_WIDTH = 1200
MAX_IMAGE_HEIGHT = 1500
JPEG_QUALITY = 65


class SiteBuilder:
    """Emits document content into an Eleventy project and builds the site."""

    def __init__(self, config: FicheritoConfig, base_url: str = "/"):
        """Initialize the site builder.

        Args:
            config: Ficherito configuration.
            base_url: Path prefix the site is served under (e.g. '/repo/').
        """
        self.config = config
        self.base_url = base_url
        self.eleventy_dir = Path(config.output.eleventy_dir)
        self.content_dir = self.eleventy_dir / "src" / "documents"
        self.images_out_dir = self.eleventy_dir / "src" / "assets" / "images" / "documents"
        self.data_dir = self.eleventy_dir / "src" / "_data"

    def build(self, enable_search: bool = True) -> Path:
        """Emit content and build the Eleventy site.

        Args:
            enable_search: Whether to run Pagefind indexing.

        Returns:
            Path to the built site (Eleventy's output directory).
        """
        self._ensure_scaffold()

        documents = self._load_documents()
        documents = sort_by_date(documents, date_key="date")

        consolidated_entities = self._load_consolidated_entities()

        self._clean_content()
        self._write_documents(documents)
        self._write_data_files(consolidated_entities)

        site_dir = self._run_eleventy(enable_search=enable_search and self.config.website.enable_search)

        logger.info(f"Site built to {site_dir}")
        return site_dir

    def _ensure_scaffold(self) -> None:
        """Copy the bundled Eleventy scaffold into place on first run."""
        if self.eleventy_dir.exists():
            return
        shutil.copytree(SCAFFOLD_DIR, self.eleventy_dir)
        logger.info(f"Created Eleventy site scaffold at {self.eleventy_dir}")

    def _clean_content(self) -> None:
        """Remove previously emitted content (but keep the scaffold's own files)."""
        if self.content_dir.exists():
            for md_file in self.content_dir.glob("*.md"):
                md_file.unlink()
        self.content_dir.mkdir(parents=True, exist_ok=True)

        if self.images_out_dir.exists():
            shutil.rmtree(self.images_out_dir)
        self.images_out_dir.mkdir(parents=True, exist_ok=True)

    def _load_documents(self) -> list[dict]:
        """Load all processed documents."""
        transcriptions_dir = Path(self.config.output.transcriptions_dir)
        translations_dir = Path(self.config.output.translations_dir)
        entities_dir = Path(self.config.output.entities_dir)

        if not transcriptions_dir.exists():
            return []

        raw = []
        for txt_file in sorted(transcriptions_dir.glob("*.md")):
            doc_id = txt_file.stem
            text, _metadata = load_transcription(txt_file)

            translation_text = None
            translation_file = translations_dir / f"{doc_id}.md"
            if translation_file.exists():
                from ficherito.translation.translator import load_translation
                translation_text, _ = load_translation(translation_file)

            entities = []
            entity_file = entities_dir / f"{doc_id}.json"
            if entity_file.exists():
                result = load_entities(entity_file)
                entities = [
                    {"text": e.text, "type": e.type, "context": e.context}
                    for e in result.entities
                ]

            raw.append({
                "id": doc_id,
                "filename": f"{doc_id}.jpg",
                "filename_date": extract_date_from_filename(doc_id),
                "transcription": text,
                "translation": translation_text,
                "entities": entities,
            })

        # If every page resolves to the same filename date, the filename is
        # encoding the whole volume's date range (e.g. a multi-page diary
        # named "Diary_19431017-19450922_IMG_003"), not this page's date.
        # Fall back to dates written in each page's own transcribed text,
        # carrying the date forward across pages that don't have one.
        filename_dates = {d["filename_date"] for d in raw if d["filename_date"]}
        volume_wide_naming = len(raw) > 1 and len(filename_dates) == 1

        documents = []
        previous_date = raw[0]["filename_date"] if raw and volume_wide_naming else None
        for doc in raw:
            if volume_wide_naming:
                date = infer_document_date(doc["transcription"], previous_date)
            else:
                date = extract_full_date_from_text(doc["transcription"]) or doc["filename_date"]
            previous_date = date

            documents.append({
                "id": doc["id"],
                "filename": doc["filename"],
                "date": date,
                "date_display": format_date_display(date),
                "transcription": doc["transcription"],
                "translation": doc["translation"],
                "entities": doc["entities"],
            })

        return documents

    def _load_consolidated_entities(self) -> dict:
        """Load consolidated entities."""
        entities_dir = Path(self.config.output.entities_dir)
        consolidated_path = entities_dir / "consolidated.json"

        if consolidated_path.exists():
            with open(consolidated_path, encoding="utf-8") as f:
                return json.load(f)

        results = []
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.json"):
                if entity_file.name != "consolidated.json":
                    try:
                        results.append(load_entities(entity_file))
                    except Exception:
                        pass

        if results:
            return consolidate_entities(results)

        return {"total_entities": 0, "unique_texts": 0, "by_type": {}, "all_entities": []}

    def _write_documents(self, documents: list[dict]) -> None:
        """Compress images and write a frontmatter + Markdown file per document."""
        default_tab = self.config.translate.default_tab if self.config.translate.enabled else "transcription"
        target_language = self.config.translate.target_language

        for i, doc in enumerate(documents):
            self._copy_image(doc["id"])

            frontmatter = {
                "title": doc["id"],
                "id": doc["id"],
                "date": doc["date"],
                "date_display": doc["date_display"],
                "image": f"{doc['id']}.jpg",
                "order": i,
                "prev": documents[i - 1]["id"] if i > 0 else None,
                "next": documents[i + 1]["id"] if i < len(documents) - 1 else None,
                "entities": doc["entities"],
                "translation": doc["translation"],
                "default_tab": default_tab,
                "target_language": target_language,
            }
            frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

            content = "---\n" + yaml.dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + doc["transcription"]
            (self.content_dir / f"{doc['id']}.md").write_text(content, encoding="utf-8")

    def _copy_image(self, doc_id: str) -> None:
        """Compress and copy a document's source image into the Eleventy assets dir."""
        possible_dirs = [Path("images"), Path("data/images")]
        dst_path = self.images_out_dir / f"{doc_id}.jpg"

        for src_dir in possible_dirs:
            for ext in [".jpg", ".jpeg", ".png", ".tiff", ".webp"]:
                src_path = src_dir / f"{doc_id}{ext}"
                if src_path.exists():
                    try:
                        self._compress_image(src_path, dst_path)
                    except Exception as e:
                        logger.warning(f"Failed to compress {src_path}: {e}, copying original")
                        shutil.copy2(src_path, dst_path)
                    return

    def _compress_image(self, src_path: Path, dst_path: Path) -> None:
        """Compress an image, resize if needed, and save as JPEG."""
        with Image.open(src_path) as img:
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            width, height = img.size
            if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
                ratio = min(MAX_IMAGE_WIDTH / width, MAX_IMAGE_HEIGHT / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            img.save(dst_path, "JPEG", quality=JPEG_QUALITY, optimize=True)

    def _write_data_files(self, consolidated_entities: dict) -> None:
        """Write the site/entities global data files consumed by 11ty templates."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        site_data = {
            "title": self.config.website.title,
            "emoji": self.config.website.emoji,
            "background_color": self.config.website.background_color,
            "accent_color": self.config.website.accent_color,
            "password": self.config.website.password,
            "enable_search": self.config.website.enable_search,
            "enable_browse_dates": self.config.website.enable_browse_dates,
            "enable_browse_entities": self.config.website.enable_browse_entities,
            "default_sort": self.config.website.default_sort,
        }
        (self.data_dir / "site.json").write_text(
            json.dumps(site_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (self.data_dir / "allEntities.json").write_text(
            json.dumps(consolidated_entities, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _run_eleventy(self, enable_search: bool) -> Path:
        """Install dependencies (if needed) and run the Eleventy build."""
        output_dir = self.eleventy_dir / "_site"
        npm_cmd = shutil.which("npm")

        if not npm_cmd:
            logger.warning(
                "npm not found; skipping Eleventy/Pagefind build. "
                "Install Node.js, then run: npm --prefix %s install && npm --prefix %s run build",
                self.eleventy_dir, self.eleventy_dir,
            )
            return output_dir

        node_modules = self.eleventy_dir / "node_modules"
        if not node_modules.exists():
            logger.info("Installing site dependencies (npm install)...")
            subprocess.run([npm_cmd, "install"], cwd=self.eleventy_dir, check=True)

        env = {
            "PATH_PREFIX": self.base_url,
            "ENABLE_SEARCH": "true" if enable_search else "false",
        }
        import os
        full_env = {**os.environ, **env}

        logger.info("Running Eleventy build...")
        result = subprocess.run(
            [npm_cmd, "run", "build"], cwd=self.eleventy_dir, env=full_env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Eleventy build failed (exit code {result.returncode})")

        return output_dir


def build_site(
    config: FicheritoConfig,
    base_url: str = "/",
    enable_search: bool = True,
) -> Path:
    """Build the static site.

    Args:
        config: Ficherito configuration.
        base_url: Path prefix the site is served under.
        enable_search: Whether to enable Pagefind search.

    Returns:
        Path to built site.
    """
    builder = SiteBuilder(config, base_url)
    return builder.build(enable_search=enable_search)
