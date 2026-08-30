"""Image processing utilities."""

from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image


def load_image(source: str | Path | bytes | BytesIO) -> Image.Image:
    """Load an image from various sources.

    Args:
        source: Path, bytes, or BytesIO containing image data.

    Returns:
        PIL Image object.

    Raises:
        ValueError: If source type is not supported.
    """
    if isinstance(source, (str, Path)):
        return Image.open(source)
    elif isinstance(source, bytes):
        return Image.open(BytesIO(source))
    elif isinstance(source, BytesIO):
        return Image.open(source)
    else:
        raise ValueError(f"Unsupported image source type: {type(source)}")


def prepare_for_ocr(
    image: Image.Image,
    max_size: Optional[Tuple[int, int]] = None,
    convert_to_rgb: bool = True,
) -> Image.Image:
    """Prepare an image for OCR processing.

    Args:
        image: Input image.
        max_size: Optional maximum dimensions (width, height).
        convert_to_rgb: Convert to RGB mode.

    Returns:
        Processed image.
    """
    img = image.copy()

    # Convert to RGB if needed
    if convert_to_rgb and img.mode not in ("RGB", "L"):
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # Handle transparency by compositing on white background. A
            # paletted image (mode "P", e.g. GIF/PNG-8) needs converting to
            # RGBA first so its transparency becomes an alpha channel/mask
            # rather than being dropped straight to black by a plain
            # convert("RGB").
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert("RGB")

    # Resize if too large
    if max_size:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

    return img


def get_image_info(image: Image.Image) -> dict:
    """Get information about an image.

    Args:
        image: PIL Image object.

    Returns:
        Dictionary with image information.
    """
    return {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
    }


def create_thumbnail(
    image: Image.Image,
    size: Tuple[int, int] = (200, 200),
) -> Image.Image:
    """Create a thumbnail of an image.

    Args:
        image: Input image.
        size: Maximum thumbnail dimensions.

    Returns:
        Thumbnail image.
    """
    thumb = image.copy()
    thumb.thumbnail(size, Image.Resampling.LANCZOS)
    return thumb


def save_image_for_web(
    image: Image.Image,
    output_path: Path,
    quality: int = 85,
    max_size: Optional[Tuple[int, int]] = (2000, 2000),
) -> Path:
    """Save an image optimized for web display.

    Args:
        image: Input image.
        output_path: Path to save to.
        quality: JPEG quality (1-100).
        max_size: Maximum dimensions.

    Returns:
        Path to saved image.
    """
    img = prepare_for_ocr(image, max_size=max_size, convert_to_rgb=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as JPEG for smaller file size
    if output_path.suffix.lower() not in (".jpg", ".jpeg"):
        output_path = output_path.with_suffix(".jpg")

    img.save(output_path, "JPEG", quality=quality, optimize=True)
    return output_path
