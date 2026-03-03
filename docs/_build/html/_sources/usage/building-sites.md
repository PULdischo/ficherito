# Building Sites

Learn how to build and customize your document collection website.

---

## Building Your Site

After processing documents, build the static website:

```bash
flatfish build
```

This creates a complete website in the `_site/` directory.

---

## What Gets Built

```
_site/
├── index.html              # Home page with collection overview
├── main.html               # Main document browser
├── overview/
│   ├── summary.html        # Finding aid
│   ├── timeline.html       # Interactive timeline
│   ├── changes.html        # Key changes
│   └── questions.html      # Research questions
├── entities/
│   └── index.html          # Entity browser
├── css/
│   └── style.css           # Styles
├── js/
│   └── app.js              # Interactive features
├── pagefind/               # Search index
└── images/                 # Document images
```

---

## Site Features

### Document Browser

Browse all documents with:
- **Image viewer** - See the original document
- **Transcription** - Read the extracted text
- **Entities** - See highlighted people, places, dates
- **Navigation** - Previous/next buttons

### Full-Text Search

Search across all transcriptions:
- Powered by [Pagefind](https://pagefind.app/)
- Instant results as you type
- Highlights matching text
- Works completely offline

### Entity Index

Browse entities by type:
- Click any entity to see all documents mentioning it
- Filter by entity type
- See context descriptions

### Overview Pages

Dropdown menu with:
- **Finding Aid** - Archival collection description
- **Timeline** - Chronological events
- **Key Changes** - Transformations over time
- **Research Questions** - Scholarly questions

---

## Previewing Your Site

Start a local preview server:

```bash
flatfish serve
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

```{tip}
The server automatically reloads when you rebuild. Keep it running in one terminal while you make changes in another.
```

### Preview Options

```bash
# Use a different port
flatfish serve --port 3000

# Open browser automatically
flatfish serve --open
```

---

## Customizing the Site

### Site Title and Description

```yaml
# flatfish.yaml
website:
  title: "Smith Family Papers"
  description: "Letters and documents from the Smith family, 1850-1920"
```

### Password Protection

Protect your site with a simple password:

```yaml
website:
  password: "research2024"
```

Users will see a login page before accessing the site.

```{note}
This is basic protection suitable for sharing with collaborators. For sensitive materials, use additional access controls on your hosting platform.
```

### Custom CSS

Add your own styles:

```yaml
website:
  custom_css: "custom.css"
```

Create `custom.css` in your project directory:

```css
/* custom.css */

/* Change header color */
.site-header {
  background-color: #2c5282;
}

/* Customize fonts */
body {
  font-family: "Georgia", serif;
}

/* Style entity highlights */
.entity-person {
  background-color: #fef3c7;
}

.entity-location {
  background-color: #dbeafe;
}
```

### Show/Hide Sections

Control which sections appear:

```yaml
website:
  show_timeline: true
  show_entities: true
  show_summary: true
  show_key_changes: false  # Hide this section
```

---

## Rebuilding After Changes

### After Editing Transcriptions

```bash
flatfish build
```

### After Editing Summaries

```bash
flatfish build
```

### After Changing Configuration

```bash
flatfish build
```

### Full Rebuild

```bash
rm -rf _site/
flatfish build
```

---

## Build Output Options

### Custom Output Directory

```bash
flatfish build --output ./my-site
```

Or in configuration:

```yaml
output:
  site_dir: "public"  # Build to ./public instead of ./_site
```

### Base URL for Subdirectories

If hosting at a subdirectory (e.g., `example.com/documents/`):

```bash
flatfish build --base-url /documents/
```

---

## Understanding the Search Index

Flatfish uses [Pagefind](https://pagefind.app/) for search:

### What's Indexed

- All transcription text
- Entity names and contexts
- Document metadata (dates, IDs)

### Search Features

- Instant results
- Highlighted matches
- Relevance ranking
- Works offline (no server needed)

### Rebuilding the Index

The search index is rebuilt automatically with `flatfish build`. If search seems broken:

```bash
rm -rf _site/pagefind/
flatfish build
```

---

## Site Performance

### Image Optimization

Flatfish automatically:
- Resizes images for web display
- Creates thumbnails for navigation
- Lazy loads images to improve performance

### For Very Large Collections

Sites with thousands of documents may need optimization:

```yaml
website:
  # Paginate document list
  documents_per_page: 100
  
  # Don't include full images in build
  inline_images: false
```

---

## Hosting Considerations

The built site is completely static:

- **No server-side code** - Just HTML, CSS, and JavaScript
- **No database** - Everything is in files
- **Works offline** - Can be viewed from local files

This means you can host it anywhere:
- [Netlify](deployment.md#deploying-to-netlify) (recommended)
- GitHub Pages
- Amazon S3
- Any web server

---

## Accessibility

Flatfish sites are designed with accessibility in mind:

- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation
- High contrast text
- Alt text for images

### Improving Accessibility

Add alt text to your transcriptions:

```json
{
  "cleaned_text": "...",
  "alt_text": "Handwritten letter dated April 15, 1863, two pages, cursive script"
}
```

---

## Troubleshooting

### Site Won't Build

**Error:** `Transcriptions not found`

Make sure you've run `flatfish extract` first.

### Search Not Working

Check that the Pagefind files exist:

```bash
ls _site/pagefind/
```

If missing, rebuild:

```bash
flatfish build
```

### Images Not Showing

Check that images are in the right location:

```bash
ls _site/images/
```

If missing, make sure `output.images_dir` in config matches where images were saved.

### CSS Not Loading

Clear browser cache and reload. Or check browser developer tools for 404 errors.

---

## Next Steps

- **[Deployment](deployment.md)** - Put your site on the web
- **[Troubleshooting](../help/troubleshooting.md)** - Solve common problems
- **[Command Reference](../commands/build.md)** - Full build options
