# Creating a Dataset

This guide shows you how to create a Hugging Face dataset from a folder of document images so you can use it with Flatfish.

---

## Overview

Flatfish uses [Hugging Face Datasets](https://huggingface.co/docs/datasets) to manage document images. If you have a folder of scanned documents or photographs, you'll need to convert them into a dataset format that Flatfish can process.

**What you'll learn:**
- How to create a dataset from a local folder of images
- How to upload your dataset to Hugging Face Hub
- How to configure Flatfish to use your dataset

---

## Prerequisites

Install the required packages:

```bash
pip install datasets huggingface_hub pillow
```

Log in to Hugging Face (you'll need a free account at [huggingface.co](https://huggingface.co)):

```bash
huggingface-cli login
```

---

## Step 1: Organize Your Images

Place all your document images in a single folder. Supported formats include:
- `.jpg` / `.jpeg`
- `.png`
- `.tiff` / `.tif`
- `.webp`

Example folder structure:
```
my_documents/
├── page_001.jpg
├── page_002.jpg
├── page_003.jpg
├── letter_1923_front.png
├── letter_1923_back.png
└── diary_entry_001.tiff
```

---

## Step 2: Create the Dataset

### Option A: Quick Script (Recommended)

Create a Python script called `create_dataset.py`:

```python
from datasets import Dataset, Features, Image, Value
from pathlib import Path
from PIL import Image as PILImage

# Configure these paths
IMAGE_FOLDER = "my_documents"  # Your folder of images
DATASET_NAME = "your-username/my-documents"  # Your HF username/dataset-name

def create_dataset_from_folder(folder_path: str) -> Dataset:
    """Create a Hugging Face dataset from a folder of images."""
    folder = Path(folder_path)
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'}
    image_files = sorted([
        f for f in folder.iterdir() 
        if f.suffix.lower() in image_extensions
    ])
    
    if not image_files:
        raise ValueError(f"No images found in {folder_path}")
    
    print(f"Found {len(image_files)} images")
    
    # Build dataset records
    records = []
    for img_path in image_files:
        records.append({
            "image": str(img_path),
            "name": img_path.stem,  # Filename without extension
        })
    
    # Create dataset with proper features
    dataset = Dataset.from_dict(
        {
            "image": [r["image"] for r in records],
            "name": [r["name"] for r in records],
        },
        features=Features({
            "image": Image(),
            "name": Value("string"),
        })
    )
    
    return dataset

# Create and push the dataset
dataset = create_dataset_from_folder(IMAGE_FOLDER)
print(dataset)
print(dataset[0])  # Preview first record

# Push to Hugging Face Hub
dataset.push_to_hub(DATASET_NAME, private=True)
print(f"\n✅ Dataset uploaded to: https://huggingface.co/datasets/{DATASET_NAME}")
```

Run the script:

```bash
python create_dataset.py
```

### Option B: With Additional Metadata

If you have dates or other metadata, you can include them:

```python
from datasets import Dataset, Features, Image, Value
from pathlib import Path
import re

IMAGE_FOLDER = "my_documents"
DATASET_NAME = "your-username/my-documents"

def extract_date_from_filename(filename: str) -> str:
    """Extract date from filename like 'diary_1923-05-15_page1.jpg'."""
    # Adjust this regex pattern to match your filenames
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return ""

def create_dataset_with_metadata(folder_path: str) -> Dataset:
    folder = Path(folder_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'}
    image_files = sorted([
        f for f in folder.iterdir() 
        if f.suffix.lower() in image_extensions
    ])
    
    records = {
        "image": [],
        "name": [],
        "date": [],
    }
    
    for img_path in image_files:
        records["image"].append(str(img_path))
        records["name"].append(img_path.stem)
        records["date"].append(extract_date_from_filename(img_path.name))
    
    dataset = Dataset.from_dict(
        records,
        features=Features({
            "image": Image(),
            "name": Value("string"),
            "date": Value("string"),
        })
    )
    
    return dataset

dataset = create_dataset_with_metadata(IMAGE_FOLDER)
dataset.push_to_hub(DATASET_NAME, private=True)
```

### Option C: From a CSV with Image Paths

If you have a CSV file listing your images and metadata:

```csv
image_path,name,date,collection
images/doc001.jpg,Letter to John,1923-05-15,correspondence
images/doc002.jpg,Diary Entry,1923-05-16,diaries
```

```python
from datasets import Dataset, Features, Image, Value
import pandas as pd

CSV_FILE = "documents.csv"
DATASET_NAME = "your-username/my-documents"

# Load CSV
df = pd.read_csv(CSV_FILE)

# Create dataset
dataset = Dataset.from_pandas(df)

# Cast the image column to Image type
dataset = dataset.cast_column("image_path", Image())
dataset = dataset.rename_column("image_path", "image")

# Push to hub
dataset.push_to_hub(DATASET_NAME, private=True)
```

---

## Step 3: Configure Flatfish

Once your dataset is uploaded, update your `flatfish.yaml`:

```yaml
dataset:
  source: "your-username/my-documents"
  splits:
    - "train"
  image_column: "image"
  id_column: "name"
  # date_column: "date"  # Uncomment if you have dates
```

---

## Step 4: Verify Your Dataset

Test that Flatfish can access your dataset:

```bash
flatfish process --limit 1
```

This will process a single document to verify everything is working.

---

## Common Issues

### "Dataset not found"

Make sure you're logged in to Hugging Face:
```bash
huggingface-cli whoami
```

If using a private dataset, ensure you have access.

### "Image column not found"

Check that your `image_column` in `flatfish.yaml` matches the column name in your dataset. You can inspect your dataset:

```python
from datasets import load_dataset
ds = load_dataset("your-username/my-documents")
print(ds["train"].column_names)
```

### Large images cause memory issues

Consider resizing images before uploading:

```python
from PIL import Image as PILImage

MAX_SIZE = 2000  # Maximum dimension

def resize_image(img_path):
    img = PILImage.open(img_path)
    if max(img.size) > MAX_SIZE:
        ratio = MAX_SIZE / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, PILImage.Resampling.LANCZOS)
        img.save(img_path)
```

---

## Working with Existing Datasets

Flatfish works with any Hugging Face dataset that has an image column. Some existing datasets you can use:

| Dataset | Description |
|---------|-------------|
| [PULdischo/marshall-diaries](https://huggingface.co/datasets/PULdischo/marshall-diaries) | Historical diary pages |
| Your own uploaded dataset | Private or public |

Browse more at [huggingface.co/datasets](https://huggingface.co/datasets).

---

## Next Steps

- [First Project](first-project.md) - Process your dataset with Flatfish
- [Configuration](../usage/configuration.md) - Full configuration reference
- [Processing Documents](../usage/processing-documents.md) - Run the full pipeline
