// The ten domains. Slugs are fixed; colours are for dots, chips, badges and the graph only,
// never inside figures. The first domain listed on a note is its primary one.

export interface Domain {
  slug: string;
  name: string;
  colour: string;
  /** Where the line falls between this domain and its neighbours. */
  boundary: string;
  /** Line-art icon: inner SVG markup on a 16px grid, stroked in currentColor. */
  icon: string;
}

// Order is the ring order on the graph: domains that share many notes sit next to each other.
export const domains: Domain[] = [
  {
    slug: 'math', name: 'Mathematics & Logic', colour: '#6aa8f0',
    boundary: 'Abstract structures. Physical application goes to the relevant science.',
    icon: '<path d="M12.5 3H4.5l4 5-4 5h8"/>',
  },
  {
    slug: 'intelligence', name: 'Intelligence & Computation', colour: '#3fd0c9',
    boundary: 'Algorithms and AI. Human cognition goes to mind.',
    icon: '<circle cx="3.5" cy="8" r="1.4"/><circle cx="12.5" cy="4" r="1.4"/><circle cx="12.5" cy="12" r="1.4"/><path d="M4.8 7.4l6.4-2.8M4.8 8.6l6.4 2.8"/>',
  },
  {
    slug: 'mind', name: 'Mind & Behavior', colour: '#f48fb1',
    boundary: 'Mental processes and behavior. Biology goes to life.',
    icon: '<path d="M5.5 13.5v-2.3C4 10.4 3 9 3 7.3 3 4.7 5.2 2.5 8 2.5s5 2.2 5 4.8c0 .9-.3 1.6-.8 2.2-.4.5-.7.9-.7 1.5v2.5zM6.5 7.5c.5-1 1.5-1 2 0s1.5 1 2 0"/>',
  },
  {
    slug: 'life', name: 'Life Sciences', colour: '#a3d65c',
    boundary: 'Biomolecules to biosphere. Engineered biology goes to tech.',
    icon: '<path d="M3 13c0-6 3.5-9.5 10-9.5 0 6.5-3.5 10-10 9.5zM3 13l5-5"/>',
  },
  {
    slug: 'earth', name: 'Earth & Space', colour: '#b39cf2',
    boundary: 'Natural cosmic and geophysical systems. Engineered space systems go to tech.',
    icon: '<circle cx="8" cy="8" r="5.5"/><path d="M2.5 8h11M8 2.5c-2 2-2 9 0 11M8 2.5c2 2 2 9 0 11"/>',
  },
  {
    slug: 'physical', name: 'Physical Sciences', colour: '#f5cf47',
    boundary: 'Matter, energy, interactions. Living systems go to life.',
    icon: '<circle cx="8" cy="8" r="1"/><ellipse cx="8" cy="8" rx="6" ry="2.4"/><ellipse cx="8" cy="8" rx="6" ry="2.4" transform="rotate(60 8 8)"/><ellipse cx="8" cy="8" rx="6" ry="2.4" transform="rotate(120 8 8)"/>',
  },
  {
    slug: 'tech', name: 'Technology & Engineering', colour: '#f58a3c',
    boundary: 'Designed systems. Pure computation goes to intelligence.',
    icon: '<g transform="scale(.6667)" stroke-width="2.25"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></g>',
  },
  {
    slug: 'economics', name: 'Economics & Finance', colour: '#4fc47f',
    boundary: 'Markets, resources, finance. Social institutions go to society.',
    icon: '<path d="M2 12l4-4 2.5 2.5L14 4.5M10.5 4.5H14V8"/>',
  },
  {
    slug: 'society', name: 'Society & Culture', colour: '#e4574d',
    boundary: 'Human collectives, history, religion, language. Individual cognition goes to mind.',
    icon: '<path d="M2.5 13.5h11M3.5 6.5h9M8 2.5l5 4H3zM5 6.5v7M8 6.5v7M11 6.5v7"/>',
  },
  {
    slug: 'arts', name: 'Creative Arts', colour: '#d975e0',
    boundary: 'Aesthetic expression. Functional engineering goes to tech.',
    icon: '<path d="M8 2.5C4.5 2.5 2.5 5 2.5 8c0 3.2 2.5 5.5 5.5 5.5 1.2 0 1.5-.8 1-1.6-.5-.9.1-1.9 1.1-1.9h1.9c.9 0 1.5-.6 1.5-1.6C13.5 4.5 11.2 2.5 8 2.5zM5.5 7.5h.01M8 5.5h.01M10.5 7h.01"/>',
  },
];

export const getDomain = (slug: string) => domains.find((d) => d.slug === slug);
export const domainSlugs = domains.map((d) => d.slug) as [string, ...string[]];

/** A domain's icon as a complete <svg> string, for scripts that build markup in the browser. */
export const iconSvg = (slug: string, size = 15) =>
  `<svg class="domain-icon" width="${size}" height="${size}" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${getDomain(slug)?.icon ?? ''}</svg>`;
