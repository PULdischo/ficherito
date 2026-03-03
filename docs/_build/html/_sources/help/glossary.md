# Glossary

Definitions of terms used in Flatfish documentation.

---

## A

### API (Application Programming Interface)
A way for software programs to communicate. Flatfish uses APIs to send document images to AI models and receive transcriptions.

### API Key
A secret code that identifies you to an API service. Required for Qwen-VL and optional for Hugging Face.

---

## B

### Batch
A group of documents processed together. Default batch size is 20 documents. Batching improves efficiency and enables progress tracking.

### Batch Combining
The process of merging individual batch summaries into a single coherent output. Uses hierarchical combining for large collections.

---

## C

### CLI (Command Line Interface)
A text-based way to interact with software. Flatfish uses CLI commands like `flatfish process` instead of a graphical interface.

### Confidence Score
A number (0-1) indicating how certain the AI model is about its output. Higher is more confident.
- 0.95+: Very confident
- 0.85-0.95: Confident
- 0.70-0.85: Uncertain
- <0.70: Low confidence

### Context Window
The maximum amount of text an AI model can process at once. Qwen-VL has ~32K tokens. Hierarchical combining addresses this limit.

---

## D

### DashScope
Alibaba Cloud's AI service platform. Hosts the Qwen-VL model used by Flatfish.

### DPI (Dots Per Inch)
A measure of image resolution. Higher DPI means more detail.
- 200 DPI: Minimum for OCR
- 300 DPI: Recommended
- 600 DPI: Archival quality

---

## E

### Entity
A named item in text, such as a person, place, date, or organization. See [Named Entities](../concepts/named-entities.md).

### Entity Linking
Connecting extracted entities to external databases like Wikidata or GeoNames.

### Entity Normalization
Mapping variant forms to a standard form. Example: "Jno. Smith" → "John Smith"

---

## F

### Finding Aid
A document describing an archival collection: what it contains, how it's organized, and how to use it. Flatfish generates finding aids automatically.

### Flatfish
This tool! A CLI for processing historical documents with AI.

---

## G

### GPE (Geo-Political Entity)
An entity type for countries, cities, states, and other political/geographic divisions. Example: "Philadelphia", "Virginia"

---

## H

### Hierarchical Combining
A technique for combining many batch summaries without exceeding API context limits. Processes batches in groups, then combines the groups.

### HTR (Handwritten Text Recognition)
The process of converting handwritten document images to digital text. More challenging than OCR due to handwriting variation.

### Hugging Face
A platform for sharing datasets and AI models. Flatfish can load document images from Hugging Face repositories.

---

## J

### Jinja2
A Python templating engine. Flatfish uses Jinja2 templates to generate HTML pages.

### JSON (JavaScript Object Notation)
A data format for storing structured information. Flatfish stores transcriptions and entities as JSON files.

---

## K

### Key Changes
One of Flatfish's summary tracks. Identifies evolving themes and tracks how they change over time.

---

## L

### LOC (Location)
An entity type for non-GPE locations like rivers, mountains, and regions. Example: "Mississippi River", "the farm"

---

## M

### Markdown
A simple text formatting language. Batch summaries are stored as Markdown files (.md).

### Model
An AI system trained to perform specific tasks. Flatfish uses:
- **Qwen-VL**: Vision-language model for transcription
- **spaCy**: NLP models for entity extraction

---

## N

### Named Entity Recognition (NER)
The process of identifying and categorizing named items (entities) in text. See [Named Entities](../concepts/named-entities.md).

### Narrative
One of Flatfish's summary tracks. Generates flowing prose describing the collection.

---

## O

### OCR (Optical Character Recognition)
The process of converting printed text images to digital text. Works on typed/printed documents.

---

## P

### Pipeline
A sequence of processing steps. Flatfish's pipeline: Transcribe → Entities → Summarize → Combine → Build.

### Prompt
Instructions given to an AI model. Flatfish uses prompts to guide transcription and summarization.

---

## Q

### Qwen-VL
A vision-language model from Alibaba. Can understand images and generate text descriptions. Used by Flatfish for transcription and summarization.

---

## R

### Research Questions
One of Flatfish's summary tracks. Identifies gaps in documentation and suggests further investigation.

---

## S

### spaCy
A Python library for natural language processing. Flatfish uses spaCy for named entity recognition.

### Static Site
A website made of plain HTML files (no server-side processing). Flatfish generates static sites that can be hosted anywhere.

### Summary Track
A specialized analysis type in Flatfish. Four tracks: Timeline, Key Changes, Research Questions, Narrative.

---

## T

### Timeline
One of Flatfish's summary tracks. Creates a chronological narrative of events mentioned in documents.

### Token
A unit of text for AI models. Roughly 4 characters or 0.75 words. API limits and pricing are often based on tokens.

### Track
See Summary Track.

### Transcription
The process of converting document images to text. Also, the resulting text itself.

### Typer
A Python library for building CLI applications. Flatfish's CLI is built with Typer.

---

## V

### Virtual Environment (venv)
An isolated Python installation. Keeps Flatfish dependencies separate from other projects.

### Vision-Language Model
An AI model that can process both images and text. Qwen-VL is a vision-language model.

---

## Y

### YAML
A human-readable data format. Flatfish configuration uses YAML files (`flatfish.yaml`).

---

## See Also

- **[FAQ](faq.md)** - Frequently asked questions
- **[Troubleshooting](troubleshooting.md)** - Problem solutions
- **[Concepts](../concepts/pipeline.md)** - How Flatfish works
