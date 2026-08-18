"""Dataset loading and handling for a local folder of document images."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from PIL import Image

from ficherito.config import FicheritoConfig
from ficherito.utils.dates import extract_date_from_filename
from ficherito.utils.logging import get_logger

logger = get_logger("dataset")

# Image file extensions recognized when scanning a local folder.
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp", ".gif", ".heic", ".heif"}

# PDF files are rendered to page images before processing.
PDF_EXTENSIONS = {".pdf"}
PDF_RENDER_DPI = 200


@dataclass
class DocumentImage:
    """Represents a single document image from the local folder."""

    image: Image.Image
    image_id: str
    filename: str
    source_path: Path
    date: str | None = None
    metadata: dict | None = None


def convert_pdfs_to_images(config: FicheritoConfig) -> list[Path]:
    """Render any PDF files in the images folder to page images using PyMuPDF.

    Each page is written next to its source PDF. Multi-page PDFs produce
    ``{stem}-p0001.png`` style names; single-page PDFs produce ``{stem}.png``.
    Existing page images are left untouched so conversion is incremental.

    Args:
        config: Ficherito configuration.

    Returns:
        Sorted list of generated (or pre-existing) page image paths.
    """
    images_dir = Path(config.dataset.images_dir)
    pattern = "**/*" if config.dataset.recursive else "*"
    pdfs = sorted(
        p
        for p in images_dir.glob(pattern)
        if p.is_file() and p.suffix.lower() in PDF_EXTENSIONS
    )
    if not pdfs:
        return []

    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PDF files were found but PyMuPDF is not installed. "
            "Install it with: pip install pymupdf"
        ) from exc

    generated: list[Path] = []
    for pdf_path in pdfs:
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.warning(f"Failed to open PDF {pdf_path.name}: {e}")
            continue

        try:
            multi_page = doc.page_count > 1
            for i, page in enumerate(doc):
                if multi_page:
                    out_path = pdf_path.parent / f"{pdf_path.stem}-p{i + 1:04d}.png"
                else:
                    out_path = pdf_path.parent / f"{pdf_path.stem}.png"

                if not out_path.exists():
                    page.get_pixmap(dpi=PDF_RENDER_DPI).save(out_path)
                    logger.debug(f"Rendered {pdf_path.name} page {i + 1} -> {out_path.name}")
                generated.append(out_path)
        finally:
            doc.close()

    return sorted(generated)


def list_image_files(config: FicheritoConfig) -> list[Path]:
    """List document image files in the configured local folder.

    Any PDF files found are first rendered to page images with PyMuPDF and
    included in the returned list.

    Args:
        config: Ficherito configuration.

    Returns:
        Sorted list of image file paths.

    Raises:
        FileNotFoundError: If the images directory does not exist.
    """
    images_dir = Path(config.dataset.images_dir)
    if not images_dir.exists():
        raise FileNotFoundError(
            f"Images directory not found: {images_dir}\n"
            "Set 'dataset.images_dir' in your config to a folder of images."
        )

    # Render PDFs to page images so they are picked up alongside regular images.
    convert_pdfs_to_images(config)

    pattern = "**/*" if config.dataset.recursive else "*"
    files = [
        p
        for p in images_dir.glob(pattern)
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def iter_document_images(
    config: FicheritoConfig,
    limit: int | None = None,
    files: list[Path] | None = None,
) -> Iterator[DocumentImage]:
    """Iterate over document images in the local folder.

    Args:
        config: Ficherito configuration.
        limit: Optional limit on number of images.
        files: Optional pre-computed list of image files.

    Yields:
        DocumentImage instances.
    """
    if files is None:
        files = list_image_files(config)

    for i, path in enumerate(files):
        if limit and i >= limit:
            break

        try:
            img = Image.open(path)
            img.load()
        except Exception:
            continue

        image_id = path.stem
        filename = path.name
        date = extract_date_from_filename(filename)

        yield DocumentImage(
            image=img,
            image_id=image_id,
            filename=filename,
            source_path=path,
            date=date,
        )


def save_image(
    doc: DocumentImage,
    output_dir: Path,
    format: str = "JPEG",
) -> Path:
    """Save a document image to disk.

    Args:
        doc: Document image to save.
        output_dir: Directory to save to.
        format: Image format (JPEG, PNG, etc.)

    Returns:
        Path to saved image.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    ext = "jpg" if format.upper() == "JPEG" else format.lower()
    output_path = output_dir / f"{doc.image_id}.{ext}"

    # Convert to RGB if necessary (for JPEG)
    img = doc.image
    if format.upper() == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(output_path, format=format)
    return output_path
