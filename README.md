# Research Toolkit

Claude Code skills for working with a Zotero library — built for social science
and humanities research on published literature.

## What's in it

| Skill | What it does |
|---|---|
| `/highlights` | Pulls your highlights and margin notes out of Zotero PDFs and organizes them by source, theme, or highlight color |
| `/code-corpus` | Thematic coding across a body of literature — build or apply a codebook, produce an evidence table, surface where sources disagree |
| `/draft-review` | Reads a draft against the sources it cites and pushes back on unsupported claims, thin evidence, and citations that don't check out |
| `/slr-screen` | Audits a systematic review corpus — reconciles stage counts, finds unscreened items, catches tag variants that split your data, produces PRISMA numbers |
| `/extract` | Framework-based extraction into a CSV evidence table using **TCCM** (theory, context, characteristics, methodology) and **CIMO** (context, intervention, mechanism, outcome) — from full texts where they exist and abstracts otherwise, recording which |

These chain together:

```
Zotero PDFs → /highlights → excerpts → /code-corpus → themes → /draft-review → critique
                                  ↑
                            /slr-screen keeps the corpus itself honest
```

## Install

If `/plugin` isn't available in your Claude Code environment, install the skills
directly instead:

```bash
./sync-local.sh
```


```bash
git clone https://github.com/lacasavita144-jpg/research-toolkit.git
```

Then in Claude Code, from the directory containing the clone:

```
/plugin marketplace add ./research-toolkit
/plugin install research-kit@research-toolkit
```

Once it's on GitHub you can skip the clone and add it directly:

```
/plugin marketplace add lacasavita144-jpg/research-toolkit
```

## Requirements

- [Zotero](https://www.zotero.org/) with a local library
- Python 3.8+ (macOS ships with this; no packages to install)

If your Zotero data lives somewhere other than `~/Zotero`, set `ZOTERO_DATA_DIR`.

## Your library is never modified

Zotero keeps its database locked while running, so `lib/zotero.py` copies the
database to a temporary file and reads that. Nothing writes back. Everything runs
locally — no library data is sent anywhere.

You can run it directly if you want to see the raw data:

```bash
python3 plugins/research-kit/lib/zotero.py stats
python3 plugins/research-kit/lib/zotero.py collections
python3 plugins/research-kit/lib/zotero.py annotations --format md
python3 plugins/research-kit/lib/zotero.py screening
python3 plugins/research-kit/lib/zotero.py queue --tag "SLR corpus"
```

## Extraction frameworks

`/extract` codes against two framework schemas, tagged per field in
`plugins/research-kit/skills/extract/schema.json`:

- **TCCM** — Theory, Context, Characteristics, Methodology.
  [Paul & Rosado-Serrano (2019)](https://doi.org/10.1108/IMR-10-2018-0280).
  Characterises the literature and surfaces gaps. Applies to nearly any study.
- **CIMO** — Context, Intervention, Mechanism, Outcome.
  [Denyer, Tranfield & van Aken (2008)](https://doi.org/10.1177/0170840607088020).
  Builds design propositions. Presupposes an actual intervention, so it does not
  apply to perception or attitude studies — a `cimo_applicable` gate field marks
  those, and the proportion that fail the gate is itself a finding.

The mechanism field is treated as inferred rather than extracted, is restricted
to full-text sources, and flags its rows for review. A table where every row has
a confident mechanism is a table where mechanisms were invented.

## Full text vs abstracts

`/extract` reads full text from Zotero's own PDF text index (`.zotero-ft-cache`),
so no PDF library is needed. Items without an attached PDF fall back to their
abstract, and every extracted row records which basis it came from. Fields marked
`requires: full-text` in `skills/extract/schema.json` are left blank rather than
guessed at for abstract-only sources.

Edit that schema to match your own review's protocol.

## A note on counts

Zotero's tag selector includes trashed items in its counts. This toolkit excludes
them everywhere, so numbers here can be substantially lower than the sidebar —
and are the ones you want for reporting. `screening` shows both.

## Known limitation

Annotations made in Preview, Acrobat, or another external PDF reader live inside
the PDF file rather than in Zotero's database, so they won't appear. To import
them, open the PDF in Zotero and use **Edit → Add Note from Annotations**.

## License

MIT
