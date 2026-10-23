import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { domainSlugs } from './data/domains';

// Limits on what shows up in the UI. Workbench keeps titles to 3 words, Alexandria allows 5; its longest description is about 230 characters.
const MAX_TITLE_WORDS = 5;
const MAX_DESCRIPTION_CHARS = 240;

const notes = defineCollection({
  // flat pool: id = slug = file name
  loader: glob({ pattern: '*.mdx', base: './src/content/notes' }),
  schema: z.object({
    /** at most 5 words, so a title always fits on a graph label and in the panel */
    title: z.string().refine((t) => t.trim().split(/\s+/).length <= MAX_TITLE_WORDS, `title must be at most ${MAX_TITLE_WORDS} words`),
    /** one sentence; the graph panel shows about 8 lines of it */
    description: z.string().max(MAX_DESCRIPTION_CHARS, `description must be at most ${MAX_DESCRIPTION_CHARS} characters`),
    /** first = primary domain; the rest are secondary */
    domains: z.array(z.enum(domainSlugs)).min(1),
    /** 3-5 one-line bullets shown in the "In short" box */
    takeaways: z.array(z.string()).default([]),
    /** what the note was written from; shown as Resources */
    sources: z
      .array(z.object({ title: z.string(), url: z.string().url(), kind: z.enum(['video', 'paper', 'blog', 'book', 'link']) }))
      .default([]),
    updated: z.coerce.date(),
  }),
});

export const collections = { notes };
