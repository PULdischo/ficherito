# Ficherito

**Transform historical document images into searchable, browsable, editable collections.**

Ficherito is a command-line tool designed for historians, archivists, librarians, and researchers who work with handwritten historical documents. It automates the process of extracting text from document images, identifying people, places, and dates, translating transcriptions, and building a searchable static website — editable afterward by collaborators through a browser, no git required.

---

## What can Ficherito do?

### 📜 Text Extraction
Extract handwritten text from document images using vision-language AI models. Ficherito preserves original spelling while cleaning up OCR errors.

### 🏷️ Entity Recognition
Automatically identify people, places, dates, organizations, and more. Each entity includes a contextual description explaining its role in the document.

### 🌍 Translation
Translate transcriptions to any language using Google Translate. Perfect for making multilingual archives accessible to wider audiences.

### 🔎 Editable Static Websites
Build a searchable, password-protected website (Eleventy + Pagefind) to share your document collection — editable afterward via Sveltia CMS and deployable to GitHub Pages.

---

## Who is this for?

Ficherito is designed for:

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
mkdir my-collection && cd my-collection
ficherito init

# Edit your configuration
nano ficherito.yaml

# Process your documents
ficherito process

# Preview your site
ficherito serve
```

That's it! You now have a searchable website of your document collection.

---

## Getting Started

New to Ficherito? Start here:

1. **[Installation](getting-started/installation.md)** - Set up your computer to run Ficherito
2. **[Quick Start](getting-started/quickstart.md)** - Process your first document collection in 10 minutes
3. **[Your First Project](getting-started/first-project.md)** - A detailed walkthrough of a complete project

---

## Need Help?

- 📖 Check the [FAQ](help/faq.md) for common questions
- 🐛 Found a bug? [Report it on GitHub](https://github.com/PULdischo/ficherito/issues)
- 💬 Questions? [Start a discussion](https://github.com/PULdischo/ficherito/discussions)
