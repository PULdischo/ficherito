# Preparing Your Images

This guide covers organizing a folder of document images for Ficherito.

---

## Overview

Ficherito reads documents from a local folder (`dataset.images_dir` in
`ficherito.yaml`, `images/` by default) — no dataset upload or hosting
service required.

---

## Step 1: Organize Your Images

Place all your document images in a single folder. Supported formats:

- `.jpg` / `.jpeg`
- `.png`
- `.tiff` / `.tif`
- `.webp`
- `.heic` / `.heif`
- `.bmp` / `.gif`
- `.pdf` (rendered to page images automatically before processing)

Example folder structure:
```
images/
├── page_001.jpg
├── page_002.jpg
├── page_003.jpg
├── letter_1923_front.png
├── letter_1923_back.png
└── diary_entry_001.tiff
```

By default Ficherito only looks in the top level of `images/`. To search
subfolders too:

```yaml
dataset:
  images_dir: "images"
  recursive: true
```

---

## Naming Your Files for Dates

Ficherito extracts dates directly from filenames (via
[undate](https://github.com/dh-tech/undate-python), which understands
partial/uncertain dates), and uses them to sort documents and drive
**Browse by Date**. Include a date if you have one:

```
# Full date
1913-01-15_page_001.jpg

# Year and month
1913-01_page_001.jpg

# Year only
1913_page_001.jpg

# No date — sorts to the end, still processed normally
diary_001.jpg
```

Recognized patterns: `YYYY-MM-DD`, `YYYYMMDD`, `YYYY-MM`, or a bare `YYYY`
anywhere in the filename.

---

## Step 2: Point Ficherito at the Folder

```yaml
# ficherito.yaml
dataset:
  images_dir: "images"
  recursive: false
```

That's it — no `id_column`, `image_column`, or upload step. The image's
filename stem (without extension) becomes the document's ID.

---

## PDFs

Multi-page PDFs are split into one image per page automatically the first
time you run `ficherito process` or `ficherito extract` — `document.pdf`
becomes `document-p0001.png`, `document-p0002.png`, etc. (single-page PDFs
become `document.png`). This requires PyMuPDF, which is installed with
Ficherito by default.

---

## Step 3: Verify

```bash
ficherito validate
ficherito process --limit 1
```

This processes a single image to confirm everything is working before you
run the full collection.

---

## Large Images

Very large scans can slow down transcription requests and increase API
cost. Consider resizing before processing if a scan exceeds a few thousand
pixels on a side:

```python
from PIL import Image

MAX_SIZE = 4000

def resize_image(img_path):
    img = Image.open(img_path)
    if max(img.size) > MAX_SIZE:
        ratio = MAX_SIZE / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(img_path)
```

(Ficherito separately compresses a resized copy of each image for the
website itself when it builds the site — this is only about the source
images sent for transcription.)

---

## Next Steps

- [First Project](first-project.md) - Process your images with Ficherito
- [Configuration](../usage/configuration.md) - Full configuration reference
- [Processing Documents](../usage/processing-documents.md) - Run the full pipeline
