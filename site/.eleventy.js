const { execSync } = require("node:child_process");
const MarkdownIt = require("markdown-it");

const md = new MarkdownIt({ html: false, breaks: true });

module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ admin: "admin" });
  eleventyConfig.addPassthroughCopy("src/assets");

  // Single newlines become <br> (matches how transcriptions were rendered
  // before), for both .md content files and the markdownify filter below.
  eleventyConfig.setLibrary("md", md);

  // Renders a raw markdown frontmatter field (e.g. a translation) to HTML.
  // Document bodies (the transcription) are rendered automatically by
  // Eleventy's own markdown engine; this filter is only for extra
  // markdown fields that live in frontmatter.
  eleventyConfig.addFilter("markdownify", (value) => (value ? md.render(value) : ""));

  eleventyConfig.addGlobalData("currentYear", () => new Date().getFullYear());

  // Groups a sorted list of document collection items by their `date` field,
  // returning [dateKey, items[]] pairs sorted by date key ("Unknown" last).
  eleventyConfig.addFilter("groupByDate", (docs) => {
    const groups = new Map();
    for (const doc of docs || []) {
      const key = doc.data.date || "Unknown";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(doc);
    }
    return Array.from(groups.entries()).sort((a, b) => {
      if (a[0] === "Unknown") return 1;
      if (b[0] === "Unknown") return -1;
      return a[0].localeCompare(b[0]);
    });
  });

  // Documents are emitted with an explicit `order` field by the Ficherito
  // Python build (based on undate-aware chronological sorting), so the
  // collection here just respects that instead of re-deriving date order.
  eleventyConfig.addCollection("documents", (collectionApi) =>
    collectionApi
      .getFilteredByTag("documents")
      .sort((a, b) => (a.data.order ?? 0) - (b.data.order ?? 0))
  );

  // Reindex Pagefind after every build, including `eleventy --serve` rebuilds.
  // Set ENABLE_SEARCH=false to skip indexing (mirrors website.enable_search).
  eleventyConfig.on("eleventy.after", () => {
    if (process.env.ENABLE_SEARCH === "false") return;
    execSync("npx pagefind --site _site", { stdio: "inherit" });
  });

  return {
    // Content bodies (transcriptions) are plain markdown, not Liquid/Nunjucks
    // templates, so don't run them through a template engine before Markdown
    // conversion (avoids misinterpreting literal `{{`/`{%` in transcribed text).
    markdownTemplateEngine: false,
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    pathPrefix: process.env.PATH_PREFIX || "/",
  };
};
