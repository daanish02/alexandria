# /// script
# requires-python = "==3.14.*"
# dependencies = [
#   "numpy==2.5.4",
# ]
# ///
"""Link audit for the notes. Adapted from Workbench's scripts/note_tools.py; it never edits anything except in `apply --write`.

  uv run scripts/links.py stats                 notes, links, per-domain table, domain-to-domain matrix, size-adjusted domain pairs, components, hubs, orphans
  uv run scripts/links.py mentions              note titles (and acronyms in titles) that a note mentions without linking to them
  uv run scripts/links.py similar               TF-IDF cosine similarity between notes that are not linked to each other
  uv run scripts/links.py compare               overlap between mentions and the top similar pairs
  uv run scripts/links.py orphans               written notes with no links either way, with the signals that say whether a link is missing
  uv run scripts/links.py apply FILE [--write]  wrap the first prose mention for each `src -> dst` line of FILE in a link (dry run unless --write)

Options: --domain D (source primary domain), --to B (target primary domain), --cross (cross-domain only), --limit N.
A note's domain is its primary one (the first in `domains`). Placeholders (notes with no body) are left out of mentions, similarity and counts.
Rules: link when the reader needs the target or it is the natural next step, first useful mention only, never to force coverage.
Read the domain-pair table (per 1000, fill%) against the within-domain fill, not against 100%.
With only a handful of notes the statistics mean little; the mention and similarity checks start paying off from about 15 notes.
Orphans that were reviewed and are fine without links go in REVIEWED_LEAVES. Aliases for mentions go in ALIASES.
"""

import argparse
import math
import pathlib
import re
import sys
from collections import Counter
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTE_ROOT = ROOT / "src" / "content" / "notes"
BASE = "/alexandria/"
DOMAIN_ORDER = re.findall(r"slug: '([a-z]+)'", (ROOT / "src" / "data" / "domains.ts").read_text(encoding="utf-8"))
# extra names for a note, keyed by slug, beyond its title and any "(ACRONYM)" in the title
ALIASES = {}
# notes that were looked at and are fine without links, keyed by slug: they stop showing as orphans
REVIEWED_LEAVES = {}
STOP = set(
    "the and for are but not you all can had her was one our out has have that this with from they will would there "
    "their what about which when your said each she how its who may into than them these then some time very been "
    "more other were also only over such most any those both after being does just like use used using make made "
    "many much well where while should could between because through before same must".split()
)
CODE = re.compile(r"```[\s\S]*?```")
MASK = re.compile(r"`[^`\n]*`|\$\$.*?\$\$|\$[^$\n]*\$|\[[^\]]*\]\([^)]*\)|<[^>]+>|https?://\S+")


def load_notes():
    notes = []
    for p in sorted(NOTE_ROOT.glob("*.mdx")):
        raw = p.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        fm, body = (m.group(1), m.group(2)) if m else ("", raw)

        def field(key):
            hit = re.search(rf"^{key}:\s*(.*?)\s*$", fm, re.M)
            return hit.group(1).strip("\"'") if hit else ""

        doms = [d.strip() for d in field("domains").strip("[]").split(",") if d.strip()]
        notes.append(SimpleNamespace(
            id=p.stem, domain=doms[0] if doms else "", title=field("title"), desc=field("description"),
            takeaways=" ".join(re.findall(r'^  - "(.*)"\s*$', fm, re.M)), body=CODE.sub("", body),
            stub=not body.strip(),
        ))
    return notes


def resolve(link):
    """Same resolution as src/lib/graph.ts: `../slug/` or the base-prefixed path, None for anything else."""
    href = link.split("#")[0]
    if not href or re.match(r"(https?:|mailto:)", href):
        return None
    if href.startswith(BASE + "notes/"):
        return href[len(BASE + "notes/"):].rstrip("/")
    m = re.match(r"^\.\./([a-z0-9-]+)/?$", href)
    return m.group(1) if m else None


def build_edges(notes):
    index = {n.id: i for i, n in enumerate(notes)}
    edges = set()
    for i, n in enumerate(notes):
        for m in re.finditer(r"\]\(([^)\s]+)\)", re.sub(r"`[^`\n]*`", "", n.body)):  # inline code is not a link, as in graph.ts
            j = index.get(resolve(m.group(1)) or "")
            if j is not None and j != i:
                edges.add((i, j))
    return edges


def clean(text, keep_links=False):
    """Prose only: drop math, inline code, tags, and (unless keep_links) the text of existing links."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1" if keep_links else " ", text)
    text = re.sub(r"\$\$.*?\$\$|\$[^$\n]*\$", " ", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    return re.sub(r"<[^>]+>", " ", text)


def stem(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def in_domain(notes, i, d):
    return notes[i].domain == d


def links_stats(notes, edges, args):
    e = set(edges)
    out, inn = Counter(a for a, _ in e), Counter(b for _, b in e)
    written = [i for i, n in enumerate(notes) if not n.stub]
    doms = [d for d in DOMAIN_ORDER if any(n.domain == d for n in notes)]
    print(f"{len(notes)} notes ({len(written)} written, {len(notes) - len(written)} placeholders), {len(e)} links\n")
    print(f"{'domain':<14}{'notes':>6}{'out/note':>9}{'in/note':>8}{'cross%':>7}{'orphans':>8}{'dead-end':>9}{'sinks':>6}")
    for d in doms:
        w = [i for i in written if notes[i].domain == d]
        de = [(x, y) for x, y in e if notes[x].domain == d]
        cross = sum(1 for x, y in de if notes[y].domain != d)
        n = max(len(w), 1)
        print(f"{d:<14}{len(w):>6}{len(de) / n:>9.1f}{sum(inn[i] for i in w) / n:>8.1f}{100 * cross / max(len(de), 1):>7.0f}"
              f"{sum(1 for i in w if not out[i] and not inn[i]):>8}{sum(1 for i in w if not out[i]):>9}{sum(1 for i in w if not inn[i]):>6}")
    print("\nlinks from row domain to column domain")
    print(f"{'':<14}" + "".join(f"{d[:10]:>11}" for d in doms))
    for a in doms:
        print(f"{a:<14}" + "".join(f"{sum(1 for x, y in e if notes[x].domain == a and notes[y].domain == b):>11}" for b in doms))
    links_by_size(notes, edges, e, written, doms)
    parent = {i: i for i in written}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for x, y in e:
        if x in parent and y in parent:
            parent[find(x)] = find(y)
    comps = {}
    for i in written:
        comps.setdefault(find(i), []).append(i)
    sizes = sorted((len(c) for c in comps.values()), reverse=True)
    print(f"\n{len(comps)} connected component(s) among written notes; sizes {sizes[:8]}")
    for c in sorted(comps.values(), key=len)[:-1][:6]:
        print("  small component:", ", ".join(notes[i].id for i in c[:6]))
    print("\ntop hubs by incoming links: " + ", ".join(f"{notes[i].id} ({inn[i]})" for i in sorted(written, key=lambda i: -inn[i])[:8]))
    orph = [notes[i].id for i in written if not out[i] and not inn[i] and notes[i].id not in REVIEWED_LEAVES]
    print(f"\norphans (no links either way, not yet reviewed): {len(orph)}; run `orphans` for the signals" + "".join(f"\n  {o}" for o in orph[:25]))


def links_by_size(notes, edges, e, written, doms):
    """Domain-pair table normalised by size, so a large domain is not read as 'more linked' just for having more notes."""
    if len(written) < 2:
        return
    sims = similar_pairs(notes, set())  # every pair, linked or not, best first
    plausible = {frozenset((p.a, p.b)) for p in sims if p.score >= 0.2}
    cands, _ = mention_candidates(notes, set(), keep_links=True)  # linked mentions count too, so linking does not shrink the set
    plausible |= {frozenset((c.src, c.dst)) for c in cands}
    linked = {frozenset(x) for x in e}
    by_dom = {d: [i for i in written if notes[i].domain == d] for d in doms}
    print("\nby domain pair, adjusted for size (each pair of notes counted once)")
    print(f"{'pair':<30}{'links':>6}{'per 1000':>9}{'A->B notes':>11}{'B->A notes':>11}{'plausible':>10}{'linked':>7}{'fill%':>6}")
    for ai, a in enumerate(doms):
        for b in doms[ai:]:
            na, nb = by_dom[a], by_dom[b]
            sa, sb = set(na), set(nb)
            pairs = len(na) * (len(na) - 1) // 2 if a == b else len(na) * len(nb)
            if not pairs:
                continue
            between = lambda x: (a == b and all(i in sa for i in x)) or (a != b and any(i in sa for i in x) and any(i in sb for i in x))
            links = sum(1 for x in linked if len(x) == 2 and between(x))
            a_to_b = sum(1 for i in na if any(x == i and y in sb and y != i for x, y in e))
            b_to_a = sum(1 for i in nb if any(x == i and y in sa and y != i for x, y in e))
            plaus = [q for q in plausible if between(q)]
            hit = sum(1 for q in plaus if q in linked)
            print(f"{a + ' - ' + b:<30}{links:>6}{1000 * links / pairs:>9.1f}{100 * a_to_b / max(len(na), 1):>10.0f}%{100 * b_to_a / max(len(nb), 1):>10.0f}%{len(plaus):>10}{hit:>7}{100 * hit / max(len(plaus), 1):>6.0f}")
    print("per 1000 = links per 1000 possible note pairs; A->B notes = share of A notes that link to any B note;")
    print("plausible = pairs with TF-IDF similarity >= 0.2 or an unlinked title mention; fill% = share of those already linked")
    out = Counter(a for a, _ in e)
    words = {i: len(re.findall(r"\w+", clean(notes[i].body, keep_links=True))) for i in written}
    dense = sorted(written, key=lambda i: -out[i])[:5]
    print("\nmost outgoing links: " + ", ".join(f"{notes[i].id} ({out[i]}, {1000 * out[i] / max(words[i], 1):.1f}/1000 words)" for i in dense))


def links_orphans(notes, edges, args):
    """For every written note with no links either way, list the signals that say whether a link is missing."""
    out, inn = Counter(a for a, _ in edges), Counter(b for _, b in edges)
    written = [i for i, n in enumerate(notes) if not n.stub]
    orphans = [i for i in written if not out[i] and not inn[i] and notes[i].id not in REVIEWED_LEAVES]
    if args.domain:
        orphans = [i for i in orphans if notes[i].domain == args.domain]
    cands, _ = mention_candidates(notes, edges)
    sims = similar_pairs(notes, edges)
    print(f"{len(orphans)} orphans to review ({len(REVIEWED_LEAVES)} already reviewed as leaves)")
    print("signals: mentioned by / mentions = titles named in the text without a link; similar = TF-IDF >= 0.12\n")
    for i in sorted(orphans, key=lambda i: notes[i].id):
        to_it = sorted((c for c in cands if c.dst == i), key=lambda c: -c.score)[:3]
        from_it = sorted((c for c in cands if c.src == i), key=lambda c: -c.score)[:3]
        sim = sorted(((p.score, p.b if p.a == i else p.a) for p in sims if i in (p.a, p.b) and p.score >= 0.12), reverse=True)[:3]
        print(f"{'check' if to_it or from_it or sim else 'likely leaf':<12} {notes[i].id}")
        print(f"    mentioned by: {[notes[c.src].id + ' [' + c.term + ']' for c in to_it]}")
        print(f"    mentions:     {[notes[c.dst].id + ' [' + c.term + ']' for c in from_it]}")
        print(f"    similar:      {[(round(s, 2), notes[j].id) for s, j in sim]}")


def links_apply(notes, edges, args):
    """Wrap the first prose mention of a target's title in a link. FILE lines: `src -> dst` or `src -> dst | regex`.
    Dry run unless --write. Skips headings, tables, code, math and text that is already a link; skips pairs already linked."""
    by_id = {n.id: n for n in notes}
    done = missed = 0
    for raw in pathlib.Path(args.pairs).read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        custom = None
        if "|" in raw:
            raw, custom = [x.strip() for x in raw.split("|", 1)]
        src, dst = [x.strip() for x in raw.split("->")]
        path = NOTE_ROOT / f"{src}.mdx"
        text = path.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in text else "\n"
        lines = text.replace("\r\n", "\n").split("\n")
        link = f"../{dst}/"
        if f"]({link})" in text:
            print(f"already linked: {src} -> {dst}")
            continue
        if custom:
            pat = re.compile(custom, re.I)
        else:
            base = re.sub(r"\s*\([^)]*\)", "", by_id[dst].title).strip()
            words = [re.escape(stem(w.lower())) + "s?" for w in re.findall(r"[A-Za-z0-9]+", base)]
            pat = re.compile(r"(?<![\w-])" + r"[\s-]+".join(words) + r"(?![\w-])", re.I)
        fences, in_code, hit = 0, False, False
        for k, line in enumerate(lines):
            if line.strip() == "---" and fences < 2:
                fences += 1
                continue
            if fences < 2:
                continue
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or line.startswith(("#", "|", "import ", "<")):
                continue
            m = pat.search(MASK.sub(lambda x: " " * len(x.group()), line))
            if not m:
                continue
            print(f"{src} -> {dst}: ...{line[max(0, m.start() - 50):m.start()]}[[{line[m.start():m.end()]}]]{line[m.end():m.end() + 40]}...")
            if args.write:
                lines[k] = line[:m.start()] + f"[{line[m.start():m.end()]}]({link})" + line[m.end():]
                path.write_bytes(nl.join(lines).encode("utf-8"))
            hit = True
            break
        done, missed = done + hit, missed + (not hit)
        if not hit:
            print(f"NO SPOT (add a sentence by hand): {src} -> {dst}")
    print(f"{done} linked, {missed} without a spot" + ("" if args.write else " (dry run; add --write to apply)"))


def mention_candidates(notes, edges, keep_links=False):
    """(source, target) pairs where the source names the target's title or acronym without linking to it."""
    lex, acr = {}, {}
    for j, n in enumerate(notes):
        if n.stub:
            continue
        base = re.sub(r"\s*\([^)]*\)", "", n.title).strip()
        names = {base, n.title, *re.findall(r"\(([A-Z][A-Za-z0-9]{1,8})\)", n.title), *ALIASES.get(n.id, [])}
        for name in names:
            ws = re.findall(r"[A-Za-z0-9]+", name)
            if len(name) < 3 or not ws:
                continue
            if len(ws) == 1 and name.isupper():
                acr.setdefault(name, set()).add(j)
            else:
                lex.setdefault(tuple(stem(w.lower()) for w in ws), set()).add(j)
    if not lex:
        return [], []
    maxn = max(len(k) for k in lex)
    hits = {}  # (source, key) -> [count, snippet]
    for i, n in enumerate(notes):
        if n.stub:
            continue
        text = clean(n.body, keep_links=keep_links)
        toks = [(m.group(), m.start(), m.end()) for m in re.finditer(r"[A-Za-z0-9]+", text)]
        low = [stem(w.lower()) for w, _, _ in toks]
        for k in range(len(toks)):
            found = []
            for size in range(1, maxn + 1):
                key = tuple(low[k:k + size])
                if len(key) == size and key in lex:
                    found.append((key, size))
            if toks[k][0] in acr:
                found.append((("ACR", toks[k][0]), 1))
            for key, size in found:
                s, e = toks[k][1], toks[k + size - 1][2]
                h = hits.setdefault((i, key), [0, " ".join(text[max(0, s - 60):e + 60].split())])
                h[0] += 1
    live = sum(1 for n in notes if not n.stub)
    df = Counter(key for _, key in hits)
    common = {key for key, c in df.items() if c > 0.15 * live}
    cands = {}
    for (i, key), (count, snippet) in hits.items():
        if key in common:
            continue
        targets = acr[key[1]] if key[0] == "ACR" else lex[key]
        weight = 1.0 if key[0] == "ACR" or len(key) > 1 else 0.5
        for j in targets:
            if j == i or (i, j) in edges:
                continue
            c = cands.setdefault((i, j), SimpleNamespace(src=i, dst=j, score=0.0, term=" ".join(key[1:] if key[0] == "ACR" else key), snippet=snippet))
            c.score += weight * count
    return list(cands.values()), sorted(" ".join(k[1:] if k[0] == "ACR" else k) for k in common)


def similar_pairs(notes, edges):
    import numpy as np

    idx = [i for i, n in enumerate(notes) if not n.stub]
    if len(idx) < 2:
        return []
    docs = []
    for i in idx:
        n = notes[i]
        text = (n.title + " ") * 3 + n.desc + " " + n.takeaways + " " + clean(n.body, keep_links=True)
        docs.append(Counter(stem(w) for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP))
    df = Counter(t for d in docs for t in d)
    size = len(docs)
    vocab = {t: k for k, t in enumerate(t for t, c in df.items() if 2 <= c <= max(0.3 * size, 2))}
    X = np.zeros((size, len(vocab)), dtype=np.float32)
    for r, d in enumerate(docs):
        for t, c in d.items():
            if t in vocab:
                X[r, vocab[t]] = (1 + math.log(c)) * (math.log((size + 1) / (df[t] + 1)) + 1)
    X /= np.linalg.norm(X, axis=1, keepdims=True).clip(min=1e-9)
    sims = X @ X.T
    words = list(vocab)
    ia, ib = np.triu_indices(size, 1)
    order = np.argsort(-sims[ia, ib])
    pairs = []
    for o in order:
        a, b = int(ia[o]), int(ib[o])
        x, y = idx[a], idx[b]
        if (x, y) in edges or (y, x) in edges:
            continue
        shared = np.argsort(-(X[a] * X[b]))[:5]
        pairs.append(SimpleNamespace(a=x, b=y, score=float(sims[a, b]), terms=[words[k] for k in shared if X[a, k] * X[b, k] > 0]))
        if len(pairs) >= 4000:
            break
    return pairs


def domain_filter(notes, args, src, dst):
    if args.domain and notes[src].domain != args.domain:
        return False
    if args.to and notes[dst].domain != args.to:
        return False
    return not args.cross or notes[src].domain != notes[dst].domain


def pair_matrix(notes, pairs):
    counts = Counter((notes[a].domain, notes[b].domain) for a, b in pairs)
    doms = [d for d in DOMAIN_ORDER if any(d in k for k in counts)]
    print(f"{'from \\ to':<14}" + "".join(f"{d[:10]:>11}" for d in doms))
    for a in doms:
        print(f"{a:<14}" + "".join(f"{counts.get((a, b), 0):>11}" for b in doms))


def links_mentions(notes, edges, args):
    cands, common = mention_candidates(notes, edges)
    cands = sorted((c for c in cands if domain_filter(notes, args, c.src, c.dst)), key=lambda c: -c.score)
    print(f"{len(cands)} unlinked mentions (source domain {args.domain or 'any'} -> target domain {args.to or 'any'}{', cross-domain' if args.cross else ''})")
    print(f"skipped as too common (in over 15% of notes): {len(common)} terms, e.g. {', '.join(common[:12])}\n")
    pair_matrix(notes, [(c.src, c.dst) for c in cands])
    print()
    for c in cands[:args.limit]:
        print(f"{c.score:5.1f}  {notes[c.src].id} -> {notes[c.dst].id}   [{c.term}]\n        ...{c.snippet}...")


def links_similar(notes, edges, args):
    pairs = [p for p in similar_pairs(notes, edges) if domain_filter(notes, args, p.a, p.b) or domain_filter(notes, args, p.b, p.a)]
    print(f"top {min(args.limit, len(pairs))} of {len(pairs)} unlinked pairs by TF-IDF cosine (domain {args.domain or 'any'} / {args.to or 'any'}{', cross-domain' if args.cross else ''})\n")
    pair_matrix(notes, [(p.a, p.b) for p in pairs[:500]])
    print("\n(counts above cover the top 500 pairs)\n")
    for p in pairs[:args.limit]:
        print(f"{p.score:.3f}  {notes[p.a].id}  <->  {notes[p.b].id}\n        shared: {', '.join(p.terms)}")


def links_compare(notes, edges, args):
    cands, _ = mention_candidates(notes, edges)
    mset = {}
    for c in cands:
        key = frozenset((c.src, c.dst))
        if key not in mset or c.score > mset[key].score:
            mset[key] = c
    sims = similar_pairs(notes, edges)[:args.limit]
    sset = {frozenset((p.a, p.b)): p for p in sims}
    both = [k for k in sset if k in mset]
    cross = lambda ks: sum(1 for k in ks if len({notes[i].domain for i in k}) > 1)
    print(f"mentions: {len(mset)} unlinked pairs ({cross(mset)} cross-domain)")
    print(f"similar:  top {len(sset)} pairs ({cross(sset)} cross-domain)")
    print(f"both:     {len(both)} pairs\n")
    show = lambda k: " <-> ".join(notes[i].id for i in sorted(k))
    print("in both (strongest evidence):")
    for k in both[:12]:
        print(f"  {sset[k].score:.3f}  {show(k)}   [{mset[k].term}; {', '.join(sset[k].terms[:3])}]")
    print("\nonly similar (no title mentioned):")
    for k in [k for k in sset if k not in mset][:12]:
        print(f"  {sset[k].score:.3f}  {show(k)}   [{', '.join(sset[k].terms[:4])}]")
    print("\nonly mentions (text not similar enough):")
    for k in sorted((k for k in mset if k not in sset), key=lambda k: -mset[k].score)[:12]:
        print(f"  {mset[k].score:4.1f}  {notes[mset[k].src].id} -> {notes[mset[k].dst].id}   [{mset[k].term}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["stats", "mentions", "similar", "compare", "orphans", "apply"])
    ap.add_argument("pairs", nargs="?")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--domain")
    ap.add_argument("--to")
    ap.add_argument("--cross", action="store_true")
    ap.add_argument("--limit", type=int, default=30)
    args = ap.parse_args()
    notes = load_notes()
    edges = build_edges(notes)
    {"stats": links_stats, "mentions": links_mentions, "similar": links_similar, "compare": links_compare, "orphans": links_orphans, "apply": links_apply}[args.mode](notes, edges, args)


if __name__ == "__main__":
    sys.exit(main())
