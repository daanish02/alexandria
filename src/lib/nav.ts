import { getCollection, type CollectionEntry } from 'astro:content';
import { paths } from '../data/paths';

export type Note = CollectionEntry<'notes'>;

/** Prefix a site-relative path with the configured base, e.g. url('log/') -> '/alexandria/log/' */
export function url(path = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const clean = path.replace(/^\//, '');
  return `${base}/${clean}`;
}

export const noteUrl = (note: Note) => url(`notes/${note.id}/`);

/** Every note, written or not. A note with no body (frontmatter only) is a placeholder: it shows on the graph as a hollow dot and its page says it is not written yet. */
export const allNotes = () => getCollection('notes');
export const isWritten = (n: Note) => (n.body ?? '').trim().length > 0;

/**
 * Estimated minutes to read a note. Technical prose is read slower than fiction (~200 wpm),
 * code slower still (~100 wpm), and each figure gets a minute to play with.
 */
export function readingMinutes(note: Note): number {
  const body = note.body ?? '';
  const code = [...body.matchAll(/```[\s\S]*?```/g)].map((m) => m[0]).join(' ');
  const figures = (body.match(/^<(?!Callout|Figure|InWords)[A-Z]\w*[^>]*\/>/gm) ?? []).length;
  const prose = body
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/\$\$[\s\S]*?\$\$/g, ' formula ')
    .replace(/<\/?[A-Z][^>]*>/g, ' ');
  const words = (s: string) => s.split(/\s+/).filter((w) => /\w/.test(w)).length;
  const takeaways = note.data.takeaways.join(' ');
  return Math.max(1, Math.round((words(prose) + words(takeaways)) / 200 + words(code) / 100 + figures));
}

/** The path a note belongs to, with its neighbours, or null. */
export function pathOf(slug: string) {
  const path = paths.find((p) => p.notes.includes(slug));
  if (!path) return null;
  const i = path.notes.indexOf(slug);
  return { path, prev: path.notes[i - 1], next: path.notes[i + 1] };
}
