---
name: extract
description: Extract structured data from a corpus of papers into an analysable table — study design, sample, country, methods, findings — reading from Zotero full texts where they exist and abstracts otherwise, recording which. Use for systematic review data extraction, building an evidence table, or characterising a body of studies.
argument-hint: [collection or tag]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write Edit
---

# Data extraction

This is the slowest stage of a review and the one where errors are least
visible, because a wrong cell in an extraction table looks exactly like a right
one. Everything below exists to make errors visible.

## Before extracting anything

Check what the corpus can actually support:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py queue --tag "SLR corpus"
```

This reports how many items offer full text and how many offer only an abstract.
Show the user those numbers and confirm the schema before starting. Extracting
300 items against the wrong field list is a day lost.

The schema lives at `${CLAUDE_SKILL_DIR}/schema.json`. Read it first. It is meant
to be edited — if the user's protocol has fields it lacks, add them there rather
than improvising per item, so the next run stays consistent.

## Getting the text

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py text --tag "SLR corpus" --limit 10
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py text --key ABCD1234
```

Each record carries a `basis` field: `full-text` or `abstract`. This governs what
you may extract, and it goes in the output table.

Work in batches of 5–10 items. Full texts run 40,000–120,000 characters, so
pulling the whole corpus at once will not fit and will fail slowly rather than
fast. Append each batch to the output file before starting the next, so an
interrupted run loses one batch rather than everything.

## The rules that make the table usable

**Never fill a cell from a source that does not contain the answer.** A field
marked `requires: full-text` in the schema stays empty for abstract-only items.
Empty is a finding — it tells the user which papers they need to obtain. A
plausible guess in that cell is indistinguishable from real data and silently
corrupts the review.

**"Not stated" and blank mean different things.** "Not stated" means you read the
source and the information is absent. Blank means you could not check. Keep them
distinct; they support different claims about the literature.

**Quote-anchor anything interpretive.** For findings, outcomes, and limitations,
carry a short verbatim phrase from the source alongside the extracted value, so
any cell can be traced back without reopening the PDF.

**Extract what the paper claims, not whether it is true.** Data extraction records
the study's own account of itself. Appraisal is a separate stage. If a paper's
claim outruns its method, that belongs in a quality-appraisal column, not in
`key_findings`.

**Flag low confidence rather than resolving it silently.** Where a paper is
ambiguous — an unclear design, a sample size that could be two different numbers
— mark the row for human review. A short list of genuinely uncertain rows is
useful; a table that looks uniformly confident when it is not is dangerous.

## Output

Write CSV, since the point is analysis elsewhere. Ask where to save it; never
write into the plugin directory. Columns, in order:

```
key, cite, basis, <schema fields...>, confidence, needs_review, notes
```

`key` is the Zotero item key, which is what makes a row traceable back to the
library months later. `basis` must never be dropped — a reviewer who cannot tell
which rows came from abstracts cannot judge the extraction.

After each batch, report progress: how many done, how many remain, and any rows
flagged for review.

## When the run finishes

Summarise honestly:

- How many rows came from full text versus abstract
- Which fields are substantially empty, and why
- Which rows need human review
- What the table can and cannot support — with 14% full-text coverage, design and
  sample fields are reasonably complete while theory and limitations are mostly
  blank, and any claim resting on those fields is not yet supportable

Then say what would most improve it. Usually that is obtaining specific missing
PDFs, and you can name exactly which ones.
