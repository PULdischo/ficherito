# Your First Project

This tutorial walks you through creating a complete Flatfish project from start to finish. We'll work with a real historical document collection and explore all of Flatfish's features.

---

## What We'll Cover

1. Understanding your source material
2. Uploading documents to Hugging Face
3. Configuring Flatfish
4. Running individual pipeline stages
5. Reviewing and editing outputs
6. Building and deploying your site

**Time needed:** 30-45 minutes

---

## Before You Begin

Make sure you have:

- [ ] Flatfish installed ([Installation Guide](installation.md))
- [ ] Your API keys ready ([Getting API Keys](installation.md#step-4-get-your-api-keys))
- [ ] A collection of document images (we'll show you how to prepare these)

---

## Part 1: Preparing Your Documents

### Understanding Document Images

Flatfish works best with:

- **Clear, high-resolution scans** (300 DPI or higher)
- **Individual pages** (one document per image)
- **Common image formats** (JPEG, PNG, TIFF)
- **Consistent orientation** (upright, not rotated)

```{tip}
If your documents are in PDF format, you'll need to convert them to images first. Tools like `pdftoppm` or Adobe Acrobat can help.
```

### Naming Your Files

Good file naming helps Flatfish understand the order of your documents. We recommend including dates or sequence numbers:

```
# Good naming patterns
1913-01-15_page_001.jpg
1913-01-15_page_002.jpg
1913-01-16_page_001.jpg

# Also acceptable
diary_001.jpg
diary_002.jpg
letter_1913-01-15.jpg
```

---

## Part 2: Creating a Hugging Face Dataset

Flatfish reads documents from Hugging Face datasets. This makes it easy to share and version your collections.

### Step 1: Create a Hugging Face Account

If you haven't already, sign up at [huggingface.co](https://huggingface.co).

### Step 2: Create a New Dataset

1. Click the **+** icon in the top navigation
2. Select **New Dataset**
3. Give it a name like `my-document-collection`
4. Choose **Private** (you can make it public later)
5. Click **Create dataset**

### Step 3: Upload Your Images

The easiest way to upload is using the web interface:

1. Click **Files and versions** tab
2. Click **Add file** → **Upload files**
3. Drag and drop your images
4. Click **Commit changes**

For larger collections, use the Hugging Face CLI:

```bash
# Install the CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Upload a folder of images
huggingface-cli upload your-username/your-dataset ./images --repo-type dataset
```

### Step 4: Create a Dataset Loading Script (Optional)

For more control, create a `dataset.py` file that tells Hugging Face how to load your data:

```python
# This goes in your dataset repository
import datasets
from pathlib import Path

class MyDocuments(datasets.GeneratorBasedBuilder):
    def _info(self):
        return datasets.DatasetInfo(
            features=datasets.Features({
                "image": datasets.Image(),
                "filename": datasets.Value("string"),
                "date": datasets.Value("string"),
            })
        )

    def _split_generators(self, dl_manager):
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={"images_dir": "images/"},
            ),
        ]

    def _generate_examples(self, images_dir):
        for idx, image_path in enumerate(sorted(Path(images_dir).glob("*.jpg"))):
            # Extract date from filename if present
            date = image_path.stem.split("_")[0] if "_" in image_path.stem else ""
            yield idx, {
                "image": str(image_path),
                "filename": image_path.name,
                "date": date,
            }
```

---

## Part 3: Setting Up Your Flatfish Project

### Create the Project

```bash
cd ~/flatfish-projects
flatfish init civil-war-letters
cd civil-war-letters
```

### Configure Your API Keys

```bash
cp .env.example .env
nano .env
```

Add your keys:

```bash
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
DASHSCOPE_API_KEY=sk_xxxxxxxxxxxxx
```

### Configure the Project

Edit `flatfish.yaml`:

```yaml
# Dataset Configuration
dataset:
  source: "your-username/your-dataset-name"
  splits:
    - "train"
  image_column: "image"
  date_column: "date"  # Optional: if your dataset has dates

# Processing Options
processing:
  extract_entities: true
  entity_context: true  # Include descriptions like "Person; the letter's recipient"

# Custom Prompts (optional - defaults work well for most documents)
prompts:
  text_extraction: |
    You are a historical document transcription assistant working with 
    Civil War era letters. Given the raw OCR output from a handwritten 
    document, clean up and correct the text while:
    
    1. Preserving original 19th-century spelling conventions
    2. Maintaining original punctuation style
    3. Fixing obvious OCR errors
    4. Marking unclear portions with [?]
    
    Raw OCR text:
    {raw_text}
    
    Cleaned transcription:

# Summary Options
summary:
  enabled: true
  model: "qwen-vl-max"
  sample_size: 100  # Process up to 100 documents for summary

# Website Options
website:
  title: "Civil War Family Letters"
  description: "Letters from the Smith family, 1861-1865"
  password: "family2024"  # Optional password protection

# Output Directories
output:
  transcriptions_dir: "transcriptions"
  entities_dir: "entities"
  summaries_dir: "summaries"
  site_dir: "_site"
```

### Validate Your Configuration

```bash
flatfish validate
```

---

## Part 4: Running the Pipeline Step by Step

While `flatfish process` runs everything at once, let's go through each step individually to understand what's happening.

### Step 1: Extract Text

```bash
flatfish extract
```

This downloads images and extracts text from each one. Progress is shown in the terminal:

```
Extracting text from 50 documents...
  [1/50] 1863-04-15_page_001.jpg ✓
  [2/50] 1863-04-15_page_002.jpg ✓
  ...
```

**Output:** Transcriptions are saved to `transcriptions/` as JSON files:

```json
{
  "id": "1863-04-15_page_001",
  "date": "1863-04-15",
  "raw_text": "April 15th 1863\nDear Sarah...",
  "cleaned_text": "April 15th 1863\nDear Sarah,\n\nI write to you from camp...",
  "confidence": 0.92
}
```

### Step 2: Extract Entities

```bash
flatfish entities
```

This identifies people, places, dates, and other entities:

```
Extracting entities from 50 documents...
  [1/50] 1863-04-15_page_001.json ✓ (12 entities)
  ...
```

**Output:** Entities are saved to `entities/`:

```json
{
  "entities": [
    {
      "text": "Sarah",
      "type": "PERSON",
      "context": "Person; the recipient of the letter, likely the writer's wife"
    },
    {
      "text": "Gettysburg",
      "type": "LOCATION",
      "context": "Location; a town in Pennsylvania mentioned as the army's destination"
    }
  ]
}
```

### Step 3: Generate Summary

```bash
flatfish summarize
```

This analyzes all documents and generates:

- A timeline of events
- Key changes across documents
- Research questions

```
Generating summary from 50 documents...
  Processing batch 1/3...
  Processing batch 2/3...
  Processing batch 3/3...
  Combining batches...
✓ Summary generated
```

**Output:** Summary files in `summaries/`:

- `finding_aid.txt` - Narrative summary in archival format
- `timeline.txt` - Chronological events
- `key_changes.txt` - Changes observed across documents
- `research_questions.txt` - Suggested research questions

### Step 4: Build the Website

```bash
flatfish build
```

This generates a static website from all your processed data:

```
Building website...
  Generating document pages...
  Generating entity index...
  Generating overview pages...
  Indexing for search...
✓ Website built at _site/
```

---

## Part 5: Reviewing and Editing

### Editing Transcriptions

Sometimes the AI makes mistakes. You can edit the transcription files directly:

```bash
nano transcriptions/1863-04-15_page_001.json
```

Find the `cleaned_text` field and make corrections. Then rebuild the site:

```bash
flatfish build
```

### Editing the Summary

The summary files are designed for human editing:

```bash
# Edit the timeline
nano summaries/timeline.txt

# Edit research questions
nano summaries/research_questions.txt
```

Timeline format:
```
# One event per line: DATE | DESCRIPTION
1863-04-15 | John writes to Sarah from camp near Fredericksburg
1863-04-18 | Regiment receives orders to march north
```

After editing, rebuild:

```bash
flatfish build
```

---

## Part 6: Preview and Deploy

### Preview Locally

```bash
flatfish serve
```

Open [http://localhost:8000](http://localhost:8000) to see your site.

### Deploy to the Web

When you're ready to share your site:

```bash
# Set your Netlify credentials
export NETLIFY_TOKEN=your-token

# Deploy (first time creates a new site)
flatfish deploy

# Or deploy to an existing site
export NETLIFY_SITE_ID=your-site-id
flatfish deploy
```

Your site is now live! Flatfish will show you the URL.

---

## Summary

You've now completed a full Flatfish project! Here's what you accomplished:

- ✅ Prepared and uploaded document images
- ✅ Configured a Flatfish project
- ✅ Extracted text from historical handwriting
- ✅ Identified named entities with context
- ✅ Generated AI-powered summaries
- ✅ Built and deployed a searchable website

---

## Next Steps

- **[Configuration Deep Dive](../usage/configuration.md)** - Customize prompts and settings
- **[Working with Large Collections](../usage/processing-documents.md)** - Handle thousands of documents
- **[Troubleshooting](../help/troubleshooting.md)** - Solve common problems
