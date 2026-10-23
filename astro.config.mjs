// @ts-check
import { defineConfig } from 'astro/config';
import { unified } from '@astrojs/markdown-remark';
import mdx from '@astrojs/mdx';
import expressiveCode from 'astro-expressive-code';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// Language names for the header tab of code blocks without a title. Shell languages and plain
// text are left out: shell blocks render as a terminal, and text/diagram blocks need no header.
const LANGUAGE_LABELS = {
  python: 'Python', sql: 'SQL', typescript: 'TypeScript', ts: 'TypeScript', javascript: 'JavaScript', js: 'JavaScript',
  rust: 'Rust', go: 'Go', java: 'Java', json: 'JSON', yaml: 'YAML', cpp: 'C++', c: 'C', html: 'HTML', css: 'CSS',
};
// The header is the title's 1.9rem line plus 0.45rem padding above and below (about 46px).
// The copy button (1.75rem) is centred in it: half the leftover space, minus the 1px frame border
// that expressive-code adds to the button's offset.
const HEADER_COPY_SPACING = 'calc((1.9rem + 0.9rem - 1.75rem) / 2 - 1px)';
function languageHeaders() {
  return {
    name: 'language-headers',
    hooks: {
      // a block's language becomes its header tab, the same look as a titled block
      preprocessMetadata: ({ codeBlock }) => {
        const label = LANGUAGE_LABELS[codeBlock.language];
        if (label && !codeBlock.props.title) codeBlock.props.title = label;
      },
    },
    baseStyles: `
      .frame.has-title:not(.is-terminal) {
        --button-spacing: ${HEADER_COPY_SPACING};
        & .title { font: 600 0.8125rem/1.9rem 'Inter', system-ui, sans-serif; padding-block: 0.45rem; }
        & .copy button { width: 1.75rem; height: 1.75rem; opacity: 0.75; background: transparent; }
        & .copy button:hover, & .copy button:focus-visible { opacity: 1; }
        & .header { align-items: center; }
      }
    `,
  };
}

// KaTeX writes every formula three times (MathML, its TeX source, and the visible glyphs). Pagefind would
// index all three, so search excerpts read "ppp is log2(1/p)\log_2(1/p)...". Hide the MathML from the index.
function ignoreMathmlInSearch() {
  return (tree) => {
    const walk = (node) => {
      if (node.type === 'element' && node.properties?.className?.includes('katex-mathml')) node.properties.dataPagefindIgnore = 'all';
      node.children?.forEach(walk);
    };
    walk(tree);
  };
}

// In GitHub Actions, actions/configure-pages provides the real origin and base path.
// Locally we fall back to the project-site layout: https://<user>.github.io/alexandria/
const site = process.env.SITE_ORIGIN || 'http://localhost:4321';
const base = process.env.SITE_BASE ?? '/alexandria';

export default defineConfig({
  site,
  base,
  trailingSlash: 'always',
  markdown: {
    processor: unified({
      remarkPlugins: [remarkMath],
      rehypePlugins: [[rehypeKatex, { strict: false }], ignoreMathmlInSearch],
    }),
  },
  integrations: [
    expressiveCode({
      themes: ['github-dark-default'],
      plugins: [languageHeaders()],
      styleOverrides: {
        borderRadius: '12px',
        borderColor: '#262626',
        codeBackground: '#0b0b0b',
        codeFontFamily: "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
        codeFontSize: '0.875rem',
        frames: {
          editorBackground: '#0b0b0b',
          terminalBackground: '#0b0b0b',
          editorTabBarBackground: '#161616',
          editorActiveTabBackground: '#161616',
          editorActiveTabForeground: '#f2b84b',
          editorActiveTabBorderColor: 'transparent',
          editorActiveTabIndicatorTopColor: 'transparent',
          editorActiveTabIndicatorBottomColor: '#f2b84b',
          editorActiveTabIndicatorHeight: '2px',
          editorTabBarBorderBottomColor: '#262626',
          terminalTitlebarBackground: '#0b0b0b',
          terminalTitlebarBorderBottomColor: '#262626',
          frameBoxShadowCssValue: 'none',
        },
      },
    }),
    mdx(),
  ],
});
