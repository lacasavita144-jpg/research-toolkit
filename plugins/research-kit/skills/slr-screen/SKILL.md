---
name: slr-screen
description: Audit the state of a systematic literature review in Zotero — reconcile screening-stage counts, find items stuck between stages, catch tag variants that split your data, spot duplicate records, and produce defensible PRISMA flow numbers. Use for SLR screening, PRISMA reporting, corpus audits, or checking whether a review's counts hold together.
argument-hint: [corpus tag]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write
---

# Auditing a systematic review corpus

A systematic review lives or dies on whether its numbers reconcile. This skill
checks that they do, and finds the specific items responsible when they don't.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py screening
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py screening --tag "SLR corpus"
```

The corpus tag is auto-detected; pass `--tag` when the guess is wrong.

## Read the report in this order

**1. Trashed items still carrying the corpus tag** (`corpus_trashed`).

This is the finding that most often changes a reported number. Zotero's tag
selector counts trashed items, so the count shown in the interface can be far
higher than the live corpus. Anyone reading counts off the sidebar is reporting
inflated figures without knowing it.

Report both numbers explicitly — live and trashed — and say which belongs in the
PRISMA diagram. Trashed items usually correspond to *excluded* records, so they
are not noise: they are the exclusion arm of the flow, and their count is
reportable. Never propose emptying the trash. Those records are the audit trail.

**2. Stage shape** (`stage_shape`), before any per-stage number.

- `nested` — each stage is a subset of the previous one. This is the classic
  funnel, and stage-to-stage differences are exclusions.
- `disjoint` — stages are parallel categories, not a funnel. Items carry one or
  the other, never both. Counts do **not** subtract; they add.
- `mixed` — partial overlap. Usually means the protocol changed mid-screening or
  two people tagged differently. Worth raising directly.

Getting this wrong inverts the entire flow diagram. Never describe a `disjoint`
scheme as a funnel, and never report "excluded at stage 2" for one.

**3. Reconciliation.** Do the stage counts plus unstaged items equal the corpus?
Show the arithmetic explicitly:

```
Tier 1 (136) + Tier 2 (162) + unstaged (9) = 307 = corpus
```

If it doesn't balance, that is the headline finding. Find the discrepancy before
reporting anything else, because every downstream number inherits it.

**4. Unstaged items** (`unstaged`). In the corpus, reached by no stage tag. These
are usually genuinely un-screened — the actual work remaining. List them with
titles so they can be triaged.

**5. Tag variants** (`tag_variants`). Concepts split across capitalisations:
`Artificial intelligence` / `artificial intelligence` / `Artificial Intelligence`
are one concept counted three ways.

This silently corrupts every frequency claim in the results section. A theme
appearing in 85 papers looks minor next to one in 175, when they are the same
theme. Report the largest clusters with their combined totals, and note that
Zotero merges tags by drag-and-drop in the tag selector — the fix is manual but
quick, and it is the user's call, not an edit to make for them.

**6. Duplicates** (`duplicate_doi_groups`, `duplicate_title_groups`). Same DOI or
same normalised title on multiple records. DOI matches are near-certain
duplicates; title matches need a look, since conference and journal versions of a
paper legitimately share a title.

## PRISMA output

When asked for flow-diagram numbers, give the counts you can support and name the
ones you cannot. A Zotero library typically cannot supply *identified* (that comes
from the database searches) or *duplicates removed at import*. It can supply
screened, included per stage, and the current corpus.

Say which is which. A flow diagram with a confidently wrong number in it is worse
than one with a gap, because the gap invites a check and the wrong number does not.

## Constraints

Never modify the library — not tags, not the trash, not records. Every finding is
a recommendation for the user to act on in Zotero.

Never present a count as reportable when its provenance is unclear. If the corpus
tag is ambiguous, or stages overlap in a way the protocol doesn't explain, say so
before giving numbers. The whole value of a systematic review is that its numbers
can be defended.
