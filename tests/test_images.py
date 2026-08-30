"""Tests for image preparation utilities."""

from PIL import Image

from ficherito.utils.images import prepare_for_ocr


def test_rgba_transparency_composites_to_white():
    img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    img.paste((255, 0, 0, 255), [0, 0, 2, 2])

    result = prepare_for_ocr(img)

    assert result.mode == "RGB"
    assert result.getpixel((3, 3)) == (255, 255, 255)
    assert result.getpixel((0, 0)) == (255, 0, 0)


def test_palette_transparency_composites_to_white():
    """A paletted image (mode 'P', e.g. GIF/PNG-8) with a transparency index
    must be composited onto white like an RGBA image, not dropped straight
    to black by a bare convert("RGB")."""
    img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    img.paste((255, 0, 0, 255), [0, 0, 2, 2])
    p_img = img.convert("P", palette=Image.ADAPTIVE)
    p_img.info["transparency"] = 0

    result = prepare_for_ocr(p_img)

    assert result.mode == "RGB"
    assert result.getpixel((3, 3)) == (255, 255, 255)


def test_la_transparency_composites_to_white():
    img = Image.new("LA", (4, 4), (0, 0))

    result = prepare_for_ocr(img)

    assert result.mode == "RGB"
    assert result.getpixel((0, 0)) == (255, 255, 255)


def test_max_size_resizes():
    img = Image.new("RGB", (4000, 2000), "white")

    result = prepare_for_ocr(img, max_size=(2048, 2048))

    assert max(result.size) <= 2048
