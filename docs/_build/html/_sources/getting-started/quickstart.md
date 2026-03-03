# Quick Start

Get up and running with Flatfish in 10 minutes! This guide assumes you've already [installed Flatfish](installation.md).

---

## Overview

In this quick start, you'll:

1. Create a new Flatfish project
2. Configure it to process a sample dataset
3. Run the processing pipeline
4. Preview your generated website

---

## Step 1: Create a New Project

Open your terminal, make sure your virtual environment is activated, and create a new project:

```bash
# Navigate to your projects folder
cd ~/flatfish-projects

# Create a new project
flatfish init my-first-collection
```

This creates a new folder called `my-first-collection` with the following structure:

```
my-first-collection/
├── flatfish.yaml     # Your project configuration
├── .env.example      # Template for API keys
├── .gitignore        # Files to exclude from version control
└── README.md         # Project documentation
```

Now enter the project directory:

```bash
cd my-first-collection
```

---

## Step 2: Add Your API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Now edit the `.env` file with your favorite text editor:

```bash
nano .env
```

Add your keys:

```bash
HUGGINGFACE_TOKEN=hf_your_token_here
DASHSCOPE_API_KEY=sk_your_key_here
```

Save and exit (in nano: `Ctrl+X`, then `Y`, then `Enter`).

---

## Step 3: Configure Your Dataset

Edit `flatfish.yaml` to point to your document dataset:

```bash
nano flatfish.yaml
```

For this quick start, we'll use a sample dataset. Update the file to look like this:

```yaml
# Dataset Configuration
dataset:
  source: "PULdischo/marshall-diaries"  # Sample historical diary
  splits:
    - "train"
  image_column: "image"

# Processing Options
processing:
  extract_entities: true
  entity_context: true

# Summary Options
summary:
  enabled: true
  model: "qwen-vl-max"
  sample_size: 20  # Limit for quick testing

# Website Options
website:
  title: "Marshall Diaries"
  description: "A collection of historical diary pages"
  password: ""  # Leave empty for public access

# Output Directories
output:
  transcriptions_dir: "transcriptions"
  entities_dir: "entities"
  summaries_dir: "summaries"
  site_dir: "_site"
```

Save and exit.

---

## Step 4: Validate Your Setup

Before processing, let's make sure everything is configured correctly:

```bash
flatfish validate
```

You should see green checkmarks for each validation step:

```
✓ Configuration file found
✓ API keys configured
✓ Dataset accessible
✓ Output directories ready
```

If you see any errors, double-check your API keys and configuration.

---

## Step 5: Process Your Documents

Now for the exciting part! Run the full processing pipeline:

```bash
flatfish process
```

You'll see progress updates as Flatfish:

1. Downloads document images from the dataset
2. Extracts text from each image
3. Identifies named entities (people, places, dates)
4. Generates an AI-powered summary
5. Builds a searchable static website

```
Downloading dataset...
✓ Downloaded 100 images

Extracting text...
  Processing image 1/100...
  Processing image 2/100...
  ...
✓ Text extraction complete

Extracting entities...
  ...
✓ Entity extraction complete

Generating summary...
  Processing batch 1/5...
  ...
✓ Summary generated

Building website...
✓ Website built successfully

Done! Your site is ready at _site/
```

```{tip}
For large collections, this process can take a while. You can start with a subset by setting `sample_size` in your configuration.
```

---

## Step 6: Preview Your Site

Start the local preview server:

```bash
flatfish serve
```

You'll see:

```
Starting local server...
✓ Server running at http://localhost:8000

Press Ctrl+C to stop
```

Open your web browser and go to [http://localhost:8000](http://localhost:8000). You'll see your document collection website!

---

## What You've Built

Your website includes:

- **📄 Document Browser** - Page through all documents with images and transcriptions
- **🔍 Full-Text Search** - Search across all transcriptions
- **🏷️ Entity Index** - Browse all people, places, and dates mentioned
- **📊 Collection Overview** - AI-generated summary with timeline and research questions

---

## Next Steps

Congratulations! You've processed your first document collection. Here's what to do next:

- **[Your First Project](first-project.md)** - A deeper dive with your own documents
- **[Configuration Guide](../usage/configuration.md)** - Customize Flatfish for your needs
- **[Deployment](../usage/deployment.md)** - Share your site with the world

---

## Cleaning Up

If you want to start over or remove generated files:

```bash
# Remove all generated files
rm -rf transcriptions/ entities/ summaries/ _site/

# Or just remove the site
rm -rf _site/
```
