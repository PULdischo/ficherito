module.exports = {
  layout: "layouts/document.njk",
  tags: ["documents"],
  // `permalink` must be computed in JS, not a `{{ }}` template string: the
  // content in this directory uses markdownTemplateEngine: false (so literal
  // `{{`/`{%` in transcribed text isn't misinterpreted), which also disables
  // template-string permalinks and left every document writing to the same
  // literal `{{ page.fileSlug }}` path.
  eleventyComputed: {
    permalink: (data) => `documents/${data.page.fileSlug}/index.html`,
  },
};
