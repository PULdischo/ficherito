# flatfish build

Generate a static website from your processed documents.

---

## Usage

```bash
flatfish build [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to config file | `flatfish.yaml` |
| `--output` | `-o` | Output directory | `site/` |
| `--template` | `-t` | Template theme | `default` |
| `--force` | `-f` | Rebuild all pages | `False` |
| `--verbose` | `-v` | Verbose output | `False` |

---

## What It Does

The `build` command:

1. Reads all processed data (transcriptions, entities, summaries)
2. Applies Jinja2 templates
3. Generates static HTML pages
4. Creates navigation and search index

```
transcriptions/ ─┐
entities/       ─┼─→ build ─→ site/
output/         ─┘              ├── index.html
                                ├── documents/
                                ├── search.json
                                └── assets/
```

---

## Examples

### Build Site

```bash
flatfish build
```

### Use Custom Template

```bash
flatfish build --template minimal
```

### Force Full Rebuild

```bash
flatfish build --force
```

### Custom Output Directory

```bash
flatfish build --output public/
```

---

## Generated Site Structure

```
site/
├── index.html              # Home page
├── finding-aid/
│   └── index.html          # Finding aid/summary
├── timeline/
│   └── index.html          # Timeline view
├── documents/
│   ├── index.html          # Document list
│   ├── letter_001/
│   │   └── index.html      # Individual document
│   ├── letter_002/
│   │   └── index.html
│   └── ...
├── entities/
│   ├── index.html          # Entity browser
│   ├── persons/
│   │   └── index.html      # People index
│   ├── places/
│   │   └── index.html      # Places index
│   └── dates/
│       └── index.html      # Dates index
├── search.json             # Search index
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
└── 404.html                # Error page
```

---

## Page Types

### Home Page (`index.html`)

- Collection title and description
- Quick navigation
- Summary statistics
- Featured documents

### Finding Aid (`finding-aid/`)

- Collection overview
- Scope and content
- Organization
- Research value

### Timeline (`timeline/`)

- Chronological event display
- Date navigation
- Event details with document links

### Document Pages (`documents/`)

- Document image viewer
- Full transcription
- Entity highlights
- Related documents

### Entity Browser (`entities/`)

- Filterable entity list
- Entity detail pages
- Document connections

---

## Configuration

### flatfish.yaml Settings

```yaml
site:
  # Site metadata
  title: "Smith Family Papers"
  description: "Letters and diaries, 1865-1870"
  author: "Archives Department"
  
  # URL configuration
  base_url: "https://example.com/smith-papers/"
  
  # Template theme
  template: default
  
  # Features
  features:
    search: true
    entity_highlighting: true
    image_viewer: true
    timeline: true
    
  # Navigation
  nav:
    - title: "Home"
      url: "/"
    - title: "Finding Aid"
      url: "/finding-aid/"
    - title: "Documents"
      url: "/documents/"
    - title: "Timeline"
      url: "/timeline/"
```

### Custom CSS

```yaml
site:
  custom_css: "assets/custom.css"
```

Create `assets/custom.css`:

```css
/* Custom styles */
.document-viewer {
  max-width: 1200px;
}

.entity-person {
  color: #2563eb;
}

.entity-place {
  color: #059669;
}
```

---

## Templates

### Built-in Themes

| Theme | Description |
|-------|-------------|
| `default` | Clean, accessible design |
| `minimal` | Simplified layout |
| `scholarly` | Academic styling |
| `archival` | Traditional archive look |

### Using a Theme

```yaml
site:
  template: scholarly
```

### Custom Templates

Create your own templates:

```
templates/
├── base.html
├── index.html
├── document.html
├── entity.html
└── partials/
    ├── header.html
    ├── footer.html
    └── navigation.html
```

Configure:

```yaml
site:
  template_dir: "templates/"
```

---

## Template Variables

### Available in All Templates

```jinja
{{ site.title }}
{{ site.description }}
{{ site.base_url }}
{{ build_date }}
{{ flatfish_version }}
```

### Document Templates

```jinja
{{ document.filename }}
{{ document.transcription }}
{{ document.entities }}
{{ document.confidence }}
{{ document.image_url }}
```

### Entity Templates

```jinja
{{ entity.text }}
{{ entity.type }}
{{ entity.count }}
{{ entity.documents }}
```

---

## Search Index

### Automatic Generation

```yaml
site:
  features:
    search: true
```

### search.json Format

```json
{
  "documents": [
    {
      "id": "letter_001",
      "title": "Letter from John Smith",
      "content": "Dear Brother, I write to inform...",
      "date": "1865-03-15",
      "entities": ["John Smith", "Philadelphia"],
      "url": "/documents/letter_001/"
    }
  ]
}
```

### Client-Side Search

Built-in uses [Lunr.js](https://lunrjs.com/) for client-side search.

---

## Progress Output

```
Flatfish Build
══════════════

Building site from processed data

Pages:
  ✓ index.html
  ✓ finding-aid/index.html
  ✓ timeline/index.html
  ✓ documents/index.html
    ├── documents/letter_001/index.html
    ├── documents/letter_002/index.html
    └── ... (498 more)
  ✓ entities/index.html
    ├── entities/persons/index.html
    └── ...

Assets:
  ✓ Copied CSS (3 files)
  ✓ Copied JS (2 files)
  ✓ Generated search.json

══════════════
Build complete!
  520 pages generated
  Site size: 15.2 MB
  Output: site/
```

---

## Incremental Builds

By default, only changed files are rebuilt:

```bash
flatfish build
# Rebuilds only changed pages

flatfish build --force
# Rebuilds everything
```

### Cache Location

```
.flatfish/
└── build_cache.json
```

---

## Image Handling

### Options

```yaml
site:
  images:
    # Include full images in site
    include: true
    
    # Generate thumbnails
    thumbnails: true
    thumbnail_size: 300
    
    # Link to external source
    external_url: "https://example.com/images/"
```

### External Images

For large collections, link to external storage:

```yaml
site:
  images:
    include: false
    external_url: "https://cdn.example.com/smith-papers/"
```

---

## Accessibility

Built-in templates include:

- Semantic HTML5
- ARIA labels
- Keyboard navigation
- Skip links
- High contrast support
- Screen reader optimization

### Accessibility Checklist

```yaml
site:
  accessibility:
    # Require alt text for images
    require_alt: true
    
    # Minimum color contrast
    min_contrast: 4.5
    
    # Generate accessibility report
    audit: true
```

---

## Troubleshooting

### Build Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Template not found" | Missing template file | Check template path |
| "No documents found" | Missing transcriptions | Run `flatfish process` first |
| "Invalid config" | YAML syntax error | Check `flatfish.yaml` |

### Slow Builds

For large collections:

```yaml
site:
  # Disable features
  features:
    search: false  # Generate separately
    thumbnails: false
    
  # Limit pages
  max_document_pages: 100  # For testing
```

---

## See Also

- **[serve](serve.md)** - Preview site locally
- **[deploy](deploy.md)** - Deploy to hosting
- **[Building Sites](../usage/building-sites.md)** - Usage guide
