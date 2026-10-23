// The note graph: one node per note, one edge per internal link written in a note's body.
// Built at build time from the content collection, so it always matches the notes.
import { allNotes, isWritten, noteUrl, type Note } from './nav';

export interface GraphNode {
  id: string; // slug
  title: string;
  description: string;
  domains: string[]; // first = primary
  href: string;
  /** false for a placeholder that has not been written yet */
  written: boolean;
  /** position in the build-up animation: starts at the oldest written note and grows along links */
  rank: number;
}

export interface Graph {
  nodes: GraphNode[];
  /** [from, to] as indices into `nodes`; deduplicated, no self-links */
  edges: [number, number][];
  /** links to something that is not a note, as "from -> link" */
  broken: string[];
}

/** Resolve a markdown link written in note `fromId` to a slug, or null if it is not an internal note link. */
function resolve(link: string): string | null {
  const href = link.split('#')[0];
  if (!href || /^(https?:|mailto:)/.test(href)) return null;
  // notes live at /notes/<slug>/, so a sibling is ../<slug>/; absolute links carry the site base
  const prefix = noteUrl({ id: '' } as Note);
  if (href.startsWith(prefix)) return href.slice(prefix.length).replace(/\/$/, '');
  const m = href.match(/^\.\.\/([a-z0-9-]+)\/?$/);
  return m ? m[1] : null;
}

export async function buildGraph(): Promise<Graph> {
  const notes: Note[] = await allNotes();
  const index = new Map(notes.map((n, i) => [n.id, i]));
  const nodes: GraphNode[] = notes.map((n) => ({
    id: n.id,
    title: n.data.title,
    description: n.data.description,
    domains: n.data.domains,
    href: noteUrl(n),
    written: isWritten(n),
    rank: 0,
  }));
  const seen = new Set<string>();
  const edges: [number, number][] = [];
  const broken: string[] = [];
  notes.forEach((n, from) => {
    // markdown links only; code blocks are skipped so example URLs inside code do not count
    const body = (n.body ?? '').replace(/```[\s\S]*?```/g, '');
    for (const m of body.matchAll(/\]\(([^)\s]+)\)/g)) {
      const target = resolve(m[1]);
      if (target === null) continue;
      const to = index.get(target);
      if (to === undefined) {
        broken.push(`${n.id} -> ${m[1]}`);
        continue;
      }
      if (to === from || seen.has(`${from}|${to}`)) continue;
      seen.add(`${from}|${to}`);
      edges.push([from, to]);
    }
  });
  rankByGrowth(notes, nodes, edges);
  return { nodes, edges, broken };
}

/**
 * Order for the build-up animation. Start at the oldest written note, then repeatedly add the oldest note
 * linked to one already shown, so every new dot appears next to something that is already on screen.
 * When nothing linked is left, jump to the oldest remaining note (written ones first).
 */
function rankByGrowth(notes: Note[], nodes: GraphNode[], edges: [number, number][]) {
  const adj = nodes.map(() => new Set<number>());
  for (const [s, t] of edges) {
    adj[s].add(t);
    adj[t].add(s);
  }
  const older = (a: number, b: number) =>
    notes[a].data.updated.getTime() - notes[b].data.updated.getTime() || nodes[a].title.localeCompare(nodes[b].title);
  const left = new Set(nodes.map((_, i) => i));
  const shown = new Set<number>();
  for (let rank = 0; left.size; rank++) {
    const near = [...left].filter((i) => [...adj[i]].some((j) => shown.has(j)));
    const pool = near.length ? near : [...left].filter((i) => nodes[i].written).length ? [...left].filter((i) => nodes[i].written) : [...left];
    const next = pool.sort(older)[0];
    nodes[next].rank = rank;
    left.delete(next);
    shown.add(next);
  }
}

/** One note and the notes linked to or from it, with every link among them: the data for a neighbourhood graph. */
export function neighbourhood(g: Graph, id: string) {
  const self = g.nodes.findIndex((n) => n.id === id);
  const keep = new Set<number>([self]);
  for (const [s, t] of g.edges) {
    if (s === self) keep.add(t);
    if (t === self) keep.add(s);
  }
  const ids = [...keep].sort((a, b) => a - b);
  const at = new Map(ids.map((old, i) => [old, i]));
  return {
    nodes: ids.map((i) => g.nodes[i]),
    edges: g.edges.filter(([s, t]) => keep.has(s) && keep.has(t)).map(([s, t]) => [at.get(s)!, at.get(t)!] as [number, number]),
    home: at.get(self)!,
  };
}

/** For each note id, the notes that link to it. */
export function backlinks(g: Graph): Map<string, GraphNode[]> {
  const out = new Map<string, GraphNode[]>(g.nodes.map((n) => [n.id, []]));
  for (const [s, t] of g.edges) out.get(g.nodes[t].id)!.push(g.nodes[s]);
  return out;
}
