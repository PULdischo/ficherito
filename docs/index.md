# Flatfish

**Transform historical document images into searchable, browsable collections.**

Flatfish is a command-line tool designed for historians, archivists, librarians, and researchers who work with handwritten historical documents. It automates the process of extracting text from document images, identifying people, places, and dates, generating AI-powered summaries, and building beautiful static websites to share your collections.

---

## What can Flatfish do?

### 📜 Text Extraction
Extract handwritten text from document images using state-of-the-art AI models. Flatfish preserves original spelling while cleaning up OCR errors.

### 🏷️ Entity Recognition
Automatically identify people, places, dates, organizations, and more. Each entity includes contextual descriptions explaining its role in the document.

### 🌍 Translation
Translate transcriptions to any language using Google Translate. Perfect for making multilingual archives accessible to wider audiences.

### 📊 AI Summaries
Generate timelines, track changes across documents, and discover research questions you might not have considered.

### 🌐 Static Websites
Build searchable, password-protected websites to share your document collections with collaborators or the public.

---

## Who is this for?

Flatfish is designed for:

- **Historians** working with archival collections
- **Archivists** processing and describing collections
- **Digital humanities researchers** exploring document analysis
- **Students** learning to work with primary sources
- **Librarians** creating access to special collections

**No programming experience required!** This documentation will guide you through every step, from installation to deployment.

---

## Quick Example

```bash
# Create a new project
flatfish init my-collection

# Edit your configuration
cd my-collection
nano flatfish.yaml

# Process your documents
flatfish process

# Preview your site
flatfish serve
```

That's it! You now have a searchable website of your document collection.

---

## Getting Started

New to Flatfish? Start here:

1. **[Installation](getting-started/installation.md)** - Set up your computer to run Flatfish
2. **[Quick Start](getting-started/quickstart.md)** - Process your first document collection in 10 minutes
3. **[Your First Project](getting-started/first-project.md)** - A detailed walkthrough of a complete project

---

## Need Help?

- 📖 Check the [FAQ](help/faq.md) for common questions
- 🐛 Found a bug? [Report it on GitHub](https://github.com/PULdischo/flatfish/issues)
- 💬 Questions? [Start a discussion](https://github.com/PULdischo/flatfish/discussions)
