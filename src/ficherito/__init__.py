"""Ficherito - Historical document analysis CLI."""

__version__ = "0.1.0"

# Register HEIF/HEIC support with Pillow so Image.open handles .heic files.
try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass
