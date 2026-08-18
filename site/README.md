# site/

This is an [Eleventy](https://www.11ty.dev/) + [Pagefind](https://pagefind.app/) +
[Sveltia CMS](https://github.com/sveltia/sveltia-cms) project. It is scaffolded
once by `ficherito build` (see `src/ficherito/site/scaffold/` in the Python
package) and then owned by you — customize freely.

`ficherito build` writes document content into `src/documents/*.md`,
`src/assets/images/documents/*.jpg`, `src/_data/site.json`, and
`src/_data/entities.json` on every run, then runs `npm run build` here, which
runs Eleventy and reindexes Pagefind.

## Local development

```bash
npm install
npm start        # eleventy --serve, rebuilds + reindexes on change
```

## Editing content

Content editors can use the CMS at `/admin/` (once deployed) instead of
editing Markdown files directly — see `admin/config.yml`. It commits changes
straight to this repository via the GitHub API, which triggers a rebuild
through `.github/workflows/deploy.yml`.

Update `admin/config.yml`'s `backend.repo` and `site_url` to match your
GitHub repository before deploying.
