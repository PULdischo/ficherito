# Deployment

Learn how to publish your document collection website to the web.

---

## Deployment Options

Ficherito generates static files that can be hosted anywhere. We recommend:

| Platform | Best For | Cost |
|----------|----------|------|
| **Netlify** | Easy deployment, custom domains | Free tier available |
| **GitHub Pages** | Projects already on GitHub | Free |
| **Vercel** | Modern hosting | Free tier available |
| **Amazon S3** | Large-scale projects | Pay per use |

---

## Deploying to Netlify

Netlify is the recommended option because:
- Free tier for most projects
- Automatic HTTPS
- Custom domains
- Built-in integration with Ficherito

### Step 1: Create a Netlify Account

1. Go to [netlify.com](https://www.netlify.com/)
2. Click **Sign up**
3. Sign up with GitHub, GitLab, or email

### Step 2: Get Your Netlify Token

1. Click your profile picture → **User settings**
2. Click **Applications** in the sidebar
3. Under "Personal access tokens", click **New access token**
4. Give it a name like "ficherito"
5. Click **Generate token**
6. **Copy the token** (you won't see it again!)

### Step 3: Configure Your Token

Add to your `.env` file:

```bash
NETLIFY_TOKEN=your_token_here
```

Or set as environment variable:

```bash
export NETLIFY_TOKEN=your_token_here
```

### Step 4: Deploy

```bash
ficherito deploy
```

First deployment creates a new Netlify site:

```
Deploying to Netlify...
Creating new site...
✓ Site created: amazing-archimedes-abc123

Uploading files...
  [########################################] 100%

✓ Deployed successfully!
  URL: https://amazing-archimedes-abc123.netlify.app
```

### Step 5: Set Up for Future Deployments

Save your site ID for future deployments:

```bash
# Add to .env
NETLIFY_SITE_ID=your-site-id
```

Now `ficherito deploy` will update the same site.

---

## Custom Domain on Netlify

### Add Your Domain

1. Go to your site in Netlify dashboard
2. Click **Domain settings**
3. Click **Add custom domain**
4. Enter your domain (e.g., `documents.example.com`)
5. Follow the DNS configuration instructions

### DNS Configuration

Add these DNS records at your domain registrar:

**For apex domain (example.com):**
```
Type: A
Name: @
Value: 75.2.60.5
```

**For subdomain (docs.example.com):**
```
Type: CNAME
Name: docs
Value: your-site.netlify.app
```

### HTTPS

Netlify automatically provisions an SSL certificate. This may take a few minutes after adding your domain.

---

## Deploying to GitHub Pages

Unlike the other options here, GitHub Pages deployment does **not** run the
Ficherito Python pipeline in CI — HTR, entity extraction, and image
compression need API keys and local images, and are meant to be run once on
your machine with `ficherito build`. CI only takes the content that build
already emitted into `site/src/documents/`, `site/src/assets/images/documents/`,
and `site/src/_data/`, and re-runs Eleventy + Pagefind on it. This is also
what makes the [Sveltia CMS](#editing-content-with-sveltia-cms) workflow
possible: it commits Markdown edits straight to `site/src/documents/`, which
triggers this same rebuild.

### Step 1: Build locally and commit the site

```bash
ficherito build
git add site/
git commit -m "Build site"
```

`site/node_modules/` and `site/_site/` are gitignored; everything else under
`site/` (including the emitted document content) should be tracked.

### Step 2: Create a Repository and Push

```bash
git init                                                     # if not already a repo
git remote add origin https://github.com/yourusername/document-collection.git
git branch -M main
git push -u origin main
```

Use a **public** repository for free GitHub Pages hosting.

### Step 3: Enable GitHub Pages

1. Go to repository **Settings** → **Pages**
2. Under "Source", select **GitHub Actions**

### Step 4: Add the Workflow File

`ficherito build` scaffolds `site/` but does not add a workflow file for
you — copy this to `.github/workflows/deploy.yml`:

```yaml
name: Deploy Site to GitHub Pages

on:
  push:
    branches: [main]
    paths: ["site/**"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: site
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: site/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Determine path prefix
        id: prefix
        run: |
          if [[ "${{ github.event.repository.name }}" == *".github.io" ]]; then
            echo "value=/" >> "$GITHUB_OUTPUT"
          else
            echo "value=/${{ github.event.repository.name }}/" >> "$GITHUB_OUTPUT"
          fi

      - name: Build site
        env:
          PATH_PREFIX: ${{ steps.prefix.outputs.value }}
        run: npm run build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/_site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

```{note}
If your repository already deploys something else to GitHub Pages (like
Sphinx/MyST docs), you can't run both — GitHub Pages serves one site per
repository. Either deploy the document collection to its own repository, or
deploy the other site elsewhere (e.g. Netlify).
```

### Step 5: Push and Deploy

```bash
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Pages workflow"
git push
```

Your site will be at: `https://yourusername.github.io/document-collection/`

### Step 6: Redeploying After Pipeline Changes

Whenever you reprocess documents or edit `ficherito.yaml`, rebuild and push again:

```bash
ficherito build
git add site/
git commit -m "Rebuild site"
git push
```

---

## Editing Content with Sveltia CMS

Once deployed, `https://yourusername.github.io/document-collection/admin/`
gives collaborators a form-based editor for transcriptions, translations, and
entities — no Markdown or git knowledge required. It's configured in
`site/admin/config.yml`, which `ficherito build` scaffolds but does not
overwrite on later runs, so it's safe to keep customized.

### Step 1: Update the Backend Config

Edit `site/admin/config.yml` and replace the placeholders:

```yaml
backend:
  name: github
  repo: yourusername/document-collection # your actual repo
  branch: main
  auth_methods: [token]

site_url: https://yourusername.github.io/document-collection
```

### Step 2: Authorize GitHub Access

[Sveltia CMS](https://github.com/sveltia/sveltia-cms) authenticates via
GitHub's OAuth device flow directly against `github.com` — no separate OAuth
proxy server to run. The first time someone opens `/admin/`, they'll be
prompted to sign in with GitHub and authorize the app; they need at least
**write** access to the repository.

### Step 3: Edit and Publish

Changes made in the CMS commit directly to `site/src/documents/*.md` on the
`main` branch, which triggers the deploy workflow from
[above](#deploying-to-github-pages) automatically. There's no separate
"publish" step — a save in the CMS is a rebuild.

```{note}
The CMS edits `title`, `date`, `entities`, `translation`, and the
transcription body. `id`, `order`, `prev`, and `next` are also editable but
are normally left alone — they're set by `ficherito build` from your image
filenames and dates.
```

---

## Deploying to Amazon S3

For large collections or enterprise hosting:

### Step 1: Create S3 Bucket

```bash
aws s3 mb s3://my-documents-site
```

### Step 2: Configure for Static Hosting

```bash
aws s3 website s3://my-documents-site --index-document index.html
```

### Step 3: Upload Files

```bash
aws s3 sync site/_site/ s3://my-documents-site --acl public-read
```

### Step 4: Access Your Site

URL format: `http://my-documents-site.s3-website-us-east-1.amazonaws.com`

For custom domains and HTTPS, add CloudFront distribution.

---

## Password Protection

### Basic Password (Ficherito Built-in)

```yaml
website:
  password: "research2024"
```

This uses JavaScript-based protection. Suitable for sharing with collaborators.

### Server-Side Protection

For stronger protection, use your hosting platform's features:

**Netlify:**
Add a `netlify.toml` file:

```toml
[[headers]]
  for = "/*"
  [headers.values]
    WWW-Authenticate = "Basic realm='Restricted'"
```

Then set up Identity or Basic Auth in Netlify dashboard.

**Apache (.htaccess):**

```apache
AuthType Basic
AuthName "Restricted"
AuthUserFile /path/to/.htpasswd
Require valid-user
```

---

## Continuous Deployment

**Netlify:** connect your Git repository, set build command to
`pip install ficherito && ficherito build`, and publish directory to `site/_site`.
Every push to `main` automatically rebuilds and deploys.

**GitHub Actions:** the workflow in
[Deploying to GitHub Pages](#deploying-to-github-pages) already does this —
any push touching `site/**` (including a Sveltia CMS edit) triggers a
rebuild. Note it only re-runs Eleventy/Pagefind, not the Python pipeline; to
pick up newly processed documents you still need to run `ficherito build`
locally and push the result.

---

## Deployment Checklist

Before deploying:

- [ ] All documents processed (`ficherito status`)
- [ ] Site builds without errors (`ficherito build`)
- [ ] Site looks correct locally (`ficherito serve`)
- [ ] Password set if needed (`website.password`)
- [ ] API keys not in committed files

After deploying:

- [ ] Site loads correctly
- [ ] Search works
- [ ] Images display
- [ ] Password protection works (if enabled)

---

## Troubleshooting

### Deploy Fails: "No site ID"

Set your site ID:
```bash
export NETLIFY_SITE_ID=your-site-id
```

### Deploy Fails: "Unauthorized"

Check your Netlify token:
```bash
echo $NETLIFY_TOKEN
```

Regenerate if needed.

### Site Shows 404

Check the base URL setting:
```bash
ficherito build --base-url /your-subdirectory/
```

### Images Not Loading

Make sure images are included in the build:
```bash
ls site/_site/assets/images/documents/
```

---

## Next Steps

- **[Troubleshooting](../help/troubleshooting.md)** - Solve common problems
- **[FAQ](../help/faq.md)** - Frequently asked questions
- **[Command Reference](../commands/deploy.md)** - Full deploy options
