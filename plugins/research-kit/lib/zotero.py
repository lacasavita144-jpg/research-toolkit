#!/usr/bin/env python3
"""Read-only access to a local Zotero library.

Zotero holds a lock on its database while running, so every command here works
on a throwaway copy. Nothing in this script writes to your library.

Usage:
    zotero.py sources     [filters] [--format json|md]
    zotero.py annotations [filters] [--format json|md]
    zotero.py collections
    zotero.py tags
    zotero.py stats

Filters:
    --collection NAME   restrict to a collection (matched case-insensitively)
    --tag TAG           restrict to items carrying this tag
    --search TEXT       match title, author, publication, or abstract
    --key KEY           restrict to one item by its Zotero key
    --color NAME        annotations only: yellow, red, green, blue, purple,
                        magenta, orange, gray
    --limit N           cap the number of results
"""
import argparse
import atexit
import json
import os
import shutil
import re
import sqlite3
import sys
import tempfile

DATA_DIR = os.path.expanduser(os.environ.get("ZOTERO_DATA_DIR", "~/Zotero"))

# Zotero's highlighter palette. Researchers routinely assign meaning to colors,
# so surfacing the name (not the hex) is what makes color-coded reading legible.
COLORS = {
    "#ffd400": "yellow",
    "#ff6666": "red",
    "#5fb236": "green",
    "#2ea8e5": "blue",
    "#a28ae5": "purple",
    "#e56eee": "magenta",
    "#f19837": "orange",
    "#aaaaaa": "gray",
}

# Fallback only; the live annotationTypes table wins when present.
ANNOTATION_TYPES = {1: "highlight", 2: "note", 3: "image", 4: "ink", 5: "underline"}

FIELDS = (
    "title", "date", "publicationTitle", "bookTitle", "publisher", "place",
    "volume", "issue", "pages", "DOI", "url", "abstractNote", "extra",
)


def open_library(data_dir=DATA_DIR):
    src = os.path.join(data_dir, "zotero.sqlite")
    if not os.path.exists(src):
        sys.exit(
            "No Zotero database at %s\n"
            "Set ZOTERO_DATA_DIR if your library lives elsewhere." % src
        )
    tmp = tempfile.mkdtemp(prefix="zotero-read-")
    atexit.register(shutil.rmtree, tmp, True)
    dst = os.path.join(tmp, "zotero.sqlite")
    shutil.copy2(src, dst)
    # Copy any hot journal alongside it so SQLite can roll the copy forward to a
    # consistent state instead of erroring on a database Zotero was mid-write on.
    for suffix in ("-journal", "-wal", "-shm"):
        if os.path.exists(src + suffix):
            shutil.copy2(src + suffix, dst + suffix)
    conn = sqlite3.connect(dst)
    conn.row_factory = sqlite3.Row
    return conn


def annotation_type_map(conn):
    try:
        rows = conn.execute("SELECT * FROM annotationTypes").fetchall()
    except sqlite3.OperationalError:
        return dict(ANNOTATION_TYPES)
    out = {}
    for r in rows:
        keys = r.keys()
        tid = r[keys[0]]
        name = next((r[k] for k in keys[1:] if isinstance(r[k], str)), None)
        if name:
            out[tid] = name
    return out or dict(ANNOTATION_TYPES)


def regular_item_ids(conn, collection=None, tag=None, search=None, key=None):
    """Top-level bibliographic items: no attachments, notes, or trashed items."""
    sql = [
        "SELECT DISTINCT i.itemID FROM items i",
        "LEFT JOIN deletedItems d ON d.itemID = i.itemID",
        "LEFT JOIN itemAttachments att ON att.itemID = i.itemID",
        "LEFT JOIN itemNotes n ON n.itemID = i.itemID",
    ]
    where = ["d.itemID IS NULL", "att.itemID IS NULL", "n.itemID IS NULL"]
    params = []

    if key:
        where.append("i.key = ?")
        params.append(key)
    if collection:
        sql.append("JOIN collectionItems ci ON ci.itemID = i.itemID")
        sql.append("JOIN collections c ON c.collectionID = ci.collectionID")
        where.append("LOWER(c.collectionName) = LOWER(?)")
        params.append(collection)
    if tag:
        sql.append("JOIN itemTags it ON it.itemID = i.itemID")
        sql.append("JOIN tags t ON t.tagID = it.tagID")
        where.append("LOWER(t.name) = LOWER(?)")
        params.append(tag)
    if search:
        sql.append("LEFT JOIN itemData sd ON sd.itemID = i.itemID")
        sql.append("LEFT JOIN itemDataValues sv ON sv.valueID = sd.valueID")
        sql.append("LEFT JOIN itemCreators sic ON sic.itemID = i.itemID")
        sql.append("LEFT JOIN creators scr ON scr.creatorID = sic.creatorID")
        where.append("(sv.value LIKE ? OR scr.lastName LIKE ? OR scr.firstName LIKE ?)")
        needle = "%%%s%%" % search
        params += [needle, needle, needle]

    sql.append("WHERE " + " AND ".join(where))
    return [r["itemID"] for r in conn.execute(" ".join(sql), params)]


def _chunks(seq, size=400):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def load_fields(conn, item_ids):
    out = {i: {} for i in item_ids}
    for chunk in _chunks(item_ids):
        marks = ",".join("?" * len(chunk))
        rows = conn.execute(
            "SELECT id.itemID, f.fieldName, v.value FROM itemData id "
            "JOIN fields f ON f.fieldID = id.fieldID "
            "JOIN itemDataValues v ON v.valueID = id.valueID "
            "WHERE id.itemID IN (%s)" % marks, chunk)
        for r in rows:
            if r["fieldName"] in FIELDS:
                out[r["itemID"]][r["fieldName"]] = r["value"]
    return out


def load_creators(conn, item_ids):
    out = {i: [] for i in item_ids}
    for chunk in _chunks(item_ids):
        marks = ",".join("?" * len(chunk))
        rows = conn.execute(
            "SELECT ic.itemID, c.firstName, c.lastName, ct.creatorType "
            "FROM itemCreators ic "
            "JOIN creators c ON c.creatorID = ic.creatorID "
            "JOIN creatorTypes ct ON ct.creatorTypeID = ic.creatorTypeID "
            "WHERE ic.itemID IN (%s) ORDER BY ic.orderIndex" % marks, chunk)
        for r in rows:
            name = " ".join(p for p in (r["firstName"], r["lastName"]) if p)
            out[r["itemID"]].append({"name": name, "role": r["creatorType"]})
    return out


def load_tags(conn, item_ids):
    out = {i: [] for i in item_ids}
    for chunk in _chunks(item_ids):
        marks = ",".join("?" * len(chunk))
        rows = conn.execute(
            "SELECT it.itemID, t.name FROM itemTags it "
            "JOIN tags t ON t.tagID = it.tagID "
            "WHERE it.itemID IN (%s)" % marks, chunk)
        for r in rows:
            out[r["itemID"]].append(r["name"])
    return out


def build_sources(conn, item_ids):
    fields = load_fields(conn, item_ids)
    creators = load_creators(conn, item_ids)
    tags = load_tags(conn, item_ids)
    meta = {}
    for chunk in _chunks(item_ids):
        marks = ",".join("?" * len(chunk))
        for r in conn.execute(
            "SELECT i.itemID, i.key, t.typeName, i.dateAdded FROM items i "
            "JOIN itemTypes t ON t.itemTypeID = i.itemTypeID "
            "WHERE i.itemID IN (%s)" % marks, chunk):
            meta[r["itemID"]] = (r["key"], r["typeName"], r["dateAdded"])

    out = []
    for iid in item_ids:
        key, itype, added = meta.get(iid, (None, None, None))
        f = fields.get(iid, {})
        out.append({
            "key": key,
            "itemType": itype,
            "dateAdded": added,
            "authors": [c["name"] for c in creators.get(iid, []) if c["role"] == "author"],
            "creators": creators.get(iid, []),
            "tags": sorted(tags.get(iid, [])),
            **{k: f.get(k) for k in FIELDS},
        })
    out.sort(key=lambda s: ((s.get("authors") or [""])[0], s.get("date") or ""))
    return out


def build_annotations(conn, item_ids, color=None):
    """Annotations hang off attachments, which hang off the bibliographic item."""
    if not item_ids:
        return []
    types = annotation_type_map(conn)
    wanted_hex = None
    if color:
        wanted_hex = {h for h, n in COLORS.items() if n == color.lower()}
        if not wanted_hex:
            sys.exit("Unknown color %r. Known: %s"
                     % (color, ", ".join(sorted(set(COLORS.values())))))

    rows = []
    for chunk in _chunks(item_ids):
        marks = ",".join("?" * len(chunk))
        rows += conn.execute(
            "SELECT a.itemID, a.type, a.text, a.comment, a.color, a.pageLabel, "
            "       a.sortIndex, a.position, a.isExternal, a.authorName, "
            "       att.parentItemID AS sourceID, ann.key AS annotationKey "
            "FROM itemAnnotations a "
            "JOIN itemAttachments att ON att.itemID = a.parentItemID "
            "JOIN items ann ON ann.itemID = a.itemID "
            "LEFT JOIN deletedItems d ON d.itemID = a.itemID "
            "WHERE d.itemID IS NULL AND att.parentItemID IN (%s)" % marks, chunk)

    out = []
    for r in rows:
        if wanted_hex and (r["color"] or "").lower() not in wanted_hex:
            continue
        page = r["pageLabel"]
        if not page:
            try:
                page = json.loads(r["position"]).get("pageIndex")
                page = None if page is None else "p.%s (index)" % page
            except (ValueError, TypeError):
                page = None
        out.append({
            "sourceID": r["sourceID"],
            "key": r["annotationKey"],
            "type": types.get(r["type"], "type-%s" % r["type"]),
            "text": (r["text"] or "").strip(),
            "comment": (r["comment"] or "").strip(),
            "color": COLORS.get((r["color"] or "").lower(), r["color"]),
            "page": page,
            "sortIndex": r["sortIndex"] or "",
            "external": bool(r["isExternal"]),
        })
    out.sort(key=lambda a: a["sortIndex"])
    return out


def cite(src):
    authors = src.get("authors") or []
    if not authors:
        who = "Anon."
    elif len(authors) == 1:
        who = authors[0].split()[-1]
    elif len(authors) == 2:
        who = " & ".join(a.split()[-1] for a in authors)
    else:
        who = authors[0].split()[-1] + " et al."
    year = (src.get("date") or "n.d.")[:4]
    return "%s %s" % (who, year)


def render_sources_md(sources):
    lines = ["# Sources (%d)" % len(sources), ""]
    for s in sources:
        venue = s.get("publicationTitle") or s.get("bookTitle") or s.get("publisher") or ""
        lines.append("- **%s** — %s" % (cite(s), s.get("title") or "(untitled)"))
        detail = " · ".join(x for x in (venue, s.get("itemType"), s.get("DOI")) if x)
        if detail:
            lines.append("  %s" % detail)
        if s.get("tags"):
            lines.append("  tags: %s" % ", ".join(s["tags"]))
        lines.append("  key: `%s`" % s.get("key"))
    return "\n".join(lines)


def render_annotations_md(sources, annotations):
    by_source = {}
    for a in annotations:
        by_source.setdefault(a["sourceID"], []).append(a)
    lines = ["# Highlights (%d across %d sources)"
             % (len(annotations), len(by_source)), ""]
    for s in sources:
        items = by_source.get(s["_id"], [])
        if not items:
            continue
        lines += ["## %s — %s" % (cite(s), s.get("title") or "(untitled)"), ""]
        for a in items:
            loc = " (p. %s)" % a["page"] if a["page"] else ""
            tag = "[%s]" % a["color"] if a["color"] else ""
            if a["text"]:
                lines.append("- %s > %s%s" % (tag, a["text"], loc))
            if a["comment"]:
                lines.append("  - note: %s" % a["comment"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- screening --

STAGE_RE = re.compile(r"^(tier|stage|phase|round)\b", re.I)
CORPUS_RE = re.compile(r"corpus|screening|review set", re.I)


def norm_tag(name):
    """Collapse the differences that make one concept look like three tags."""
    return re.sub(r"[\s_-]+", " ", name.strip().lower()).rstrip(".,;:")


def norm_doi(doi):
    if not doi:
        return None
    d = doi.strip().lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    return d or None


def norm_title(title):
    if not title:
        return None
    return re.sub(r"[^a-z0-9]+", "", title.lower()) or None


def screening_report(conn, corpus_tag=None):
    ids = regular_item_ids(conn)
    tags = load_tags(conn, ids)
    fields = load_fields(conn, ids)
    creators = load_creators(conn, ids)

    all_tag_counts = {}
    for tl in tags.values():
        for t in tl:
            all_tag_counts[t] = all_tag_counts.get(t, 0) + 1

    # Which tag marks the corpus, and which mark screening stages.
    if not corpus_tag:
        cands = [t for t in all_tag_counts if CORPUS_RE.search(t)]
        corpus_tag = max(cands, key=lambda t: all_tag_counts[t]) if cands else None
    stage_tags = sorted((t for t in all_tag_counts if STAGE_RE.match(t)),
                        key=lambda t: t.lower())

    corpus_ids = [i for i in ids if corpus_tag and corpus_tag in tags[i]]
    scope = corpus_ids or ids

    stages = [{"tag": t,
               "n": sum(1 for i in scope if t in tags[i])} for t in stage_tags]

    # Items in the corpus that no stage tag has reached yet.
    unstaged = [i for i in scope if not any(t in tags[i] for t in stage_tags)]

    # Stages can be nested (each stage a subset of the last) or disjoint
    # (parallel categories). Measure which, rather than assuming: treating
    # disjoint categories as a broken pipeline invents errors that aren't there.
    overlap = []
    for a_idx in range(len(stage_tags)):
        for b_idx in range(a_idx + 1, len(stage_tags)):
            a, b = stage_tags[a_idx], stage_tags[b_idx]
            both = sum(1 for i in scope if a in tags[i] and b in tags[i])
            overlap.append({"a": a, "b": b, "both": both,
                            "only_a": sum(1 for i in scope
                                          if a in tags[i] and b not in tags[i]),
                            "only_b": sum(1 for i in scope
                                          if b in tags[i] and a not in tags[i])})
    if not overlap:
        shape = "single-stage"
    elif all(o["both"] == 0 for o in overlap):
        shape = "disjoint"
    elif all(o["both"] == min(o["both"] + o["only_a"],
                              o["both"] + o["only_b"]) for o in overlap):
        shape = "nested"
    else:
        shape = "mixed"

    # Only meaningful when stages are nested; noise otherwise.
    gaps = []
    if shape == "nested":
        for idx in range(1, len(stage_tags)):
            earlier, later = stage_tags[idx - 1], stage_tags[idx]
            for i in scope:
                if later in tags[i] and earlier not in tags[i]:
                    gaps.append({"itemID": i, "has": later, "missing": earlier})

    # Tag variants: same concept, different capitalisation or spacing. These
    # silently split counts in any frequency analysis.
    by_norm = {}
    for t, n in all_tag_counts.items():
        by_norm.setdefault(norm_tag(t), []).append((t, n))
    variants = [{"normalized": k,
                 "variants": sorted(v, key=lambda x: -x[1]),
                 "combined": sum(n for _, n in v)}
                for k, v in by_norm.items() if len(v) > 1]
    variants.sort(key=lambda d: -d["combined"])

    # Duplicate records inside the corpus.
    def dupes(keyfn):
        groups = {}
        for i in scope:
            k = keyfn(fields.get(i, {}))
            if k:
                groups.setdefault(k, []).append(i)
        return {k: v for k, v in groups.items() if len(v) > 1}

    doi_dupes = dupes(lambda f: norm_doi(f.get("DOI")))
    title_dupes = dupes(lambda f: norm_title(f.get("title")))

    def describe(i):
        f = fields.get(i, {})
        auth = [c["name"] for c in creators.get(i, []) if c["role"] == "author"]
        return {"title": f.get("title"), "date": f.get("date"),
                "authors": auth[:3], "doi": f.get("DOI")}

    trashed_tagged = 0
    if corpus_tag:
        trashed_tagged = conn.execute(
            "SELECT COUNT(*) FROM itemTags it "
            "JOIN tags t ON t.tagID = it.tagID "
            "JOIN deletedItems d ON d.itemID = it.itemID "
            "WHERE t.name = ?", (corpus_tag,)).fetchone()[0]

    return {
        "corpus_tag": corpus_tag,
        "corpus_size": len(corpus_ids) if corpus_tag else None,
        "corpus_trashed": trashed_tagged,
        "library_size": len(ids),
        "stage_shape": shape,
        "stage_overlap": overlap,
        "stages": stages,
        "unstaged_count": len(unstaged),
        "unstaged": [describe(i) for i in unstaged[:50]],
        "stage_gaps_count": len(gaps),
        "stage_gaps": [dict(describe(g["itemID"]), has=g["has"],
                            missing=g["missing"]) for g in gaps[:50]],
        "duplicate_doi_groups": [[describe(i) for i in v]
                                 for v in list(doi_dupes.values())[:25]],
        "duplicate_title_groups": [[describe(i) for i in v]
                                   for v in list(title_dupes.values())[:25]],
        "duplicate_doi_count": len(doi_dupes),
        "duplicate_title_count": len(title_dupes),
        "tag_variants": variants[:40],
        "tag_variant_count": len(variants),
    }



def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command",
                   choices=["sources", "annotations", "collections", "tags", "stats", "screening"])
    p.add_argument("--collection")
    p.add_argument("--tag")
    p.add_argument("--search")
    p.add_argument("--key")
    p.add_argument("--color")
    p.add_argument("--limit", type=int)
    p.add_argument("--format", choices=["json", "md"], default="json")
    p.add_argument("--data-dir", default=DATA_DIR)
    args = p.parse_args()

    conn = open_library(args.data_dir)

    if args.command == "screening":
        print(json.dumps(screening_report(conn, args.tag), indent=2))
        return

    if args.command == "collections":
        rows = conn.execute(
            "SELECT c.collectionName AS name, COUNT(ci.itemID) AS n "
            "FROM collections c "
            "LEFT JOIN collectionItems ci ON ci.collectionID = c.collectionID "
            "LEFT JOIN deletedItems d ON d.itemID = ci.itemID "
            "WHERE d.itemID IS NULL "
            "GROUP BY c.collectionID ORDER BY n DESC").fetchall()
        print(json.dumps([dict(r) for r in rows], indent=2))
        return

    if args.command == "tags":
        rows = conn.execute(
            "SELECT t.name, COUNT(it.itemID) AS n FROM tags t "
            "JOIN itemTags it ON it.tagID = t.tagID "
            "LEFT JOIN deletedItems d ON d.itemID = it.itemID "
            "WHERE d.itemID IS NULL "
            "GROUP BY t.tagID ORDER BY n DESC").fetchall()
        print(json.dumps([dict(r) for r in rows], indent=2))
        return

    ids = regular_item_ids(conn, args.collection, args.tag, args.search, args.key)

    if args.command == "stats":
        ann = build_annotations(conn, ids)
        by_color = {}
        for a in ann:
            by_color[a["color"]] = by_color.get(a["color"], 0) + 1
        print(json.dumps({
            "sources": len(ids),
            "annotations": len(ann),
            "sources_with_annotations": len({a["sourceID"] for a in ann}),
            "by_color": by_color,
        }, indent=2))
        return

    sources = build_sources(conn, ids)
    # re-attach internal ids for grouping
    key_to_id = {}
    for chunk in _chunks(ids):
        marks = ",".join("?" * len(chunk))
        for r in conn.execute(
                "SELECT itemID, key FROM items WHERE itemID IN (%s)" % marks, chunk):
            key_to_id[r["key"]] = r["itemID"]
    for s in sources:
        s["_id"] = key_to_id.get(s["key"])

    if args.command == "sources":
        if args.limit:
            sources = sources[:args.limit]
        print(render_sources_md(sources) if args.format == "md"
              else json.dumps(sources, indent=2))
        return

    if args.command == "annotations":
        ann = build_annotations(conn, ids, args.color)
        if args.limit:
            ann = ann[:args.limit]
        if args.format == "md":
            print(render_annotations_md(sources, ann))
        else:
            by_id = {s["_id"]: s for s in sources}
            for a in ann:
                src = by_id.get(a["sourceID"], {})
                a["source"] = {"cite": cite(src), "title": src.get("title"),
                               "key": src.get("key")}
                del a["sourceID"]
            print(json.dumps(ann, indent=2))


if __name__ == "__main__":
    main()
