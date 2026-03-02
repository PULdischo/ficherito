# Deployment

Learn how to publish your document collection website to the web.

---

## Deployment Options

Flatfish generates static files that can be hosted anywhere. We recommend:

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
- Built-in integration with Flatfish

### Step 1: Create a Netlify Account

1. Go to [netlify.com](https://www.netlify.com/)
2. Click **Sign up**
3. Sign up with GitHub, GitLab, or email

### Step 2: Get Your Netlify Token

1. Click your profile picture → **User settings**
2. Click **Applications** in the sidebar
3. Under "Personal access tokens", click **New access token**
4. Give it a name like "flatfish"
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
flatfish deploy
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

Now `flatfish deploy` will update the same site.

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

### Step 1: Create a Repository

1. Go to [github.com](https://github.com)
2. Click **New repository**
3. Name it (e.g., `document-collection`)
4. Make it public (required for free GitHub Pages)

### Step 2: Initialize Git

In your Flatfish project:

```bash
git init
git add .
git commit -m "Initial commit"
```

### Step 3: Add Remote and Push

```bash
git remote add origin https://github.com/yourusername/document-collection.git
git branch -M main
git push -u origin main
```

### Step 4: Enable GitHub Pages

1. Go to repository **Settings**
2. Click **Pages** in sidebar
3. Under "Source", select **GitHub Actions**

### Step 5: Create Workflow File

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install flatfish
      
      - name: Build site
        run: flatfish build --base-url /${{ github.event.repository.name }}/
        env:
          HUGGINGFACE_TOKEN: ${{ secrets.HUGGINGFACE_TOKEN }}
          DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
      
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./_site
```

### Step 6: Add Secrets

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Add `HUGGINGFACE_TOKEN` and `DASHSCOPE_API_KEY`

### Step 7: Push and Deploy

```bash
git add .github/
git commit -m "Add GitHub Pages workflow"
git push
```

Your site will be at: `https://yourusername.github.io/document-collection/`

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
aws s3 sync _site/ s3://my-documents-site --acl public-read
```

### Step 4: Access Your Site

URL format: `http://my-documents-site.s3-website-us-east-1.amazonaws.com`

For custom domains and HTTPS, add CloudFront distribution.

---

## Password Protection

### Basic Password (Flatfish Built-in)

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

### Auto-Deploy on Git Push

**Netlify:**
1. Connect your Git repository
2. Set build command: `pip install flatfish && flatfish build`
3. Set publish directory: `_site`

Every push to `main` automatically rebuilds and deploys.

**GitHub Actions:**
The workflow above already does this.

### Scheduled Rebuilds

To update your site regularly (e.g., if dataset changes):

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight
```

---

## Deployment Checklist

Before deploying:

- [ ] All documents processed (`flatfish status`)
- [ ] Site builds without errors (`flatfish build`)
- [ ] Site looks correct locally (`flatfish serve`)
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
flatfish build --base-url /your-subdirectory/
```

### Images Not Loading

Make sure images are included in the build:
```bash
ls _site/images/
```

---

## Next Steps

- **[Troubleshooting](../help/troubleshooting.md)** - Solve common problems
- **[FAQ](../help/faq.md)** - Frequently asked questions
- **[Command Reference](../commands/deploy.md)** - Full deploy options
