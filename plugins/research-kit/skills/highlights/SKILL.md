---
name: highlights
description: Pull highlights and margin notes out of Zotero PDFs and organize them into usable reading notes — by source, by theme, or by highlight color. Use when the user asks what they highlighted, wants their annotations from a paper or collection, or wants reading notes built from what they marked while reading.
argument-hint: [source, collection, tag, or theme]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write Glob
---

# Reading highlights out of Zotero

Your annotations already encode your thinking — what you marked, what you wrote
in the margin, what color you used. This skill turns them back into prose you
can work from.

## Getting the data

All access is read-only and runs against a throwaway copy of the library.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py annotations --format md
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py annotations --collection "Chapter 2"
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py annotations --search "Bourdieu" --format md
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py annotations --color yellow
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py stats
```

Start with `collections` or `tags` if you need to find the right filter name.
Use `stats` first when the request is vague — it shows how much material exists
before you pull it all.

## What to do with it

**Never paraphrase a highlight into the note as if it were the source's words.**
A highlight is a verbatim quotation. Keep it verbatim, in quotation marks, with
its page. The user's own margin comment is a different kind of statement — their
reaction, not the author's claim — and must stay visibly theirs.

Structure by what was asked:

- **One source** → running notes in reading order, each highlight with its page,
  the user's comments attached beneath the passage they belong to.
- **A collection or tag** → group by source, ordered by author. Open with two or
  three sentences on what the sources share and where they diverge.
- **A theme** → regroup across sources under thematic headings. This is the most
  useful and the least literal: you are reorganizing someone's reading around an
  idea, so say which sources cluster and which one sits awkwardly.

## Colors carry meaning

Researchers assign meaning to highlight colors, but the meaning is personal. If
the library uses more than two colors, show the distribution from `stats` and ask
what each stands for before organizing around them. Do not assume yellow means
important or red means disagreement.

Once known, color is a strong organizing axis — for example method notes in one
color and theoretical claims in another become two clean sections.

## When there is nothing to return

An empty result usually means one of these, so check before reporting failure:

- The PDFs were annotated in Preview, Acrobat, or Adobe rather than Zotero's own
  reader. Those annotations live in the PDF file, not the database, until they
  are imported. In Zotero: open the PDF, then **Edit → Add Note from Annotations**.
- The filter name is wrong. Run `collections` or `tags` and compare.
- The library is somewhere other than `~/Zotero`. Set `ZOTERO_DATA_DIR`.

Say which of these it is. Do not report an empty library as though the user has
not been reading.
