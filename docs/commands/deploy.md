# flatfish deploy

Deploy your generated site to a hosting platform.

---

## Usage

```bash
flatfish deploy [options]
```

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--platform` | `-p` | Hosting platform | auto-detect |
| `--site-id` | `-s` | Site identifier | from config |
| `--build` | `-b` | Build before deploy | `True` |
| `--preview` | | Deploy to preview URL | `False` |
| `--verbose` | `-v` | Verbose output | `False` |

---

## Supported Platforms

| Platform | Command | Notes |
|----------|---------|-------|
| Netlify | `--platform netlify` | Recommended |
| GitHub Pages | `--platform github` | Free for public repos |
| Vercel | `--platform vercel` | Fast global CDN |
| Cloudflare Pages | `--platform cloudflare` | Free tier available |
| Custom | `--platform custom` | Use deploy script |

---

## Examples

### Deploy to Netlify

```bash
flatfish deploy --platform netlify
```

### Deploy to GitHub Pages

```bash
flatfish deploy --platform github
```

### Preview Deployment

```bash
flatfish deploy --preview
# Creates temporary preview URL
```

### Skip Build Step

```bash
flatfish deploy --no-build
# Deploy existing site/ directory
```

---

## Platform Setup

### Netlify

#### 1. Install Netlify CLI

```bash
npm install -g netlify-cli
```

#### 2. Login to Netlify

```bash
netlify login
```

#### 3. Configure

```yaml
# flatfish.yaml
deploy:
  platform: netlify
  site_id: "your-site-id"  # Optional: link to existing site
```

#### 4. Deploy

```bash
flatfish deploy
# or
flatfish deploy --platform netlify
```

### GitHub Pages

#### 1. Enable GitHub Pages

In your repository settings:
- Go to Pages
- Select source branch (e.g., `gh-pages`)
- Select root folder

#### 2. Configure

```yaml
# flatfish.yaml
deploy:
  platform: github
  branch: gh-pages
  cname: "custom-domain.com"  # Optional
```

#### 3. Deploy

```bash
flatfish deploy --platform github
```

This will:
1. Build the site
2. Push to `gh-pages` branch
3. GitHub automatically serves the site

### Vercel

#### 1. Install Vercel CLI

```bash
npm install -g vercel
```

#### 2. Login

```bash
vercel login
```

#### 3. Deploy

```bash
flatfish deploy --platform vercel
```

### Cloudflare Pages

#### 1. Install Wrangler

```bash
npm install -g wrangler
```

#### 2. Login

```bash
wrangler login
```

#### 3. Configure

```yaml
# flatfish.yaml
deploy:
  platform: cloudflare
  project_name: "smith-papers"
```

#### 4. Deploy

```bash
flatfish deploy --platform cloudflare
```

---

## Configuration

### flatfish.yaml Settings

```yaml
deploy:
  # Platform selection
  platform: netlify
  
  # Site directory
  directory: site/
  
  # Build before deploy
  auto_build: true
  
  # Platform-specific settings
  netlify:
    site_id: "abc123"
    
  github:
    branch: gh-pages
    cname: "example.com"
    
  vercel:
    project_name: "my-project"
    
  cloudflare:
    project_name: "my-project"
```

### Environment Variables

```bash
# Netlify
NETLIFY_AUTH_TOKEN=your-token

# Vercel
VERCEL_TOKEN=your-token

# GitHub (usually automatic with git)
GITHUB_TOKEN=your-token
```

---

## Deploy Output

```
Flatfish Deploy
═══════════════

Platform: Netlify
Site ID: abc123-xyz

[1/3] Building site...
  ✓ 520 pages generated

[2/3] Uploading...
  Uploading: site/
  ████████████████████ 100%
  Uploaded 15.2 MB (520 files)

[3/3] Publishing...
  ✓ Deployed!

═══════════════
Site live at: https://smith-papers.netlify.app

Deploy ID: 65a1b2c3d4e5f6
Deploy time: 45 seconds
```

---

## Preview Deployments

Create a temporary preview without affecting production:

```bash
flatfish deploy --preview
```

Output:
```
Preview deployed to:
https://preview-abc123--smith-papers.netlify.app

This preview will expire in 24 hours.
```

Use for:
- Testing changes before production
- Sharing drafts for review
- QA testing

---

## Custom Deploy Scripts

For unsupported platforms:

```yaml
# flatfish.yaml
deploy:
  platform: custom
  script: "scripts/deploy.sh"
```

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
# Custom deployment script

# Build site
flatfish build

# Upload to your server
rsync -avz site/ user@server:/var/www/site/

# Clear cache
ssh user@server "sudo systemctl reload nginx"

echo "Deployed!"
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Site

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install Flatfish
        run: pip install flatfish
        
      - name: Build and Deploy
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
        run: |
          flatfish build
          flatfish deploy --platform netlify
```

### GitLab CI

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  script:
    - pip install flatfish
    - flatfish build
    - flatfish deploy --platform netlify
  only:
    - main
```

---

## Rollback

### Netlify

```bash
# List recent deploys
netlify deploy --list

# Rollback to previous
netlify deploy --restore <deploy-id>
```

### GitHub Pages

```bash
# Revert commit on gh-pages
git checkout gh-pages
git revert HEAD
git push
```

---

## Troubleshooting

### Authentication Errors

```
Error: Not authenticated
```

Solution:
```bash
# Re-login to platform
netlify login
# or
vercel login
```

### Build Failures

```
Error: Build failed
```

Solution:
```bash
# Build locally first
flatfish build
# Check for errors, then deploy
flatfish deploy --no-build
```

### Large File Errors

```
Error: File too large
```

Solution:
```yaml
# Reduce image sizes
site:
  images:
    external_url: "https://cdn.example.com/images/"
```

---

## See Also

- **[build](build.md)** - Generate site
- **[serve](serve.md)** - Local preview
- **[Deployment Guide](../usage/deployment.md)** - Detailed deployment instructions
