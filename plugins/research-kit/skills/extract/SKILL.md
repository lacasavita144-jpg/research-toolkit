---
name: extract
description: Framework-based data extraction from a corpus of papers into an analysable table, using TCCM (theory, context, characteristics, methodology) and CIMO (context, intervention, mechanism, outcome) logic. Reads Zotero full texts where they exist and abstracts otherwise, recording which. Use for systematic review extraction, evidence tables, characterising a literature, or building design propositions.
argument-hint: [collection or tag]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write Edit
---

# TCCM and CIMO extraction

Two frameworks doing different jobs. TCCM characterises what the literature looks
like — which theories, contexts, constructs, and methods appear, and which are
missing. CIMO builds prescriptive knowledge: in context C, intervention I invokes
mechanism M to deliver outcome O.

The schema at `${CLAUDE_SKILL_DIR}/schema.json` tags every field with its
framework and element. Read it before starting; it is meant to be edited.

## Before extracting anything

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py queue --tag "SLR corpus"
```

Report the full-text and abstract-only counts to the user and confirm the schema.
Extracting hundreds of items against the wrong field list is a day lost.

## Getting the text

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py text --tag "SLR corpus" --limit 8
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py text --key ABCD1234
```

Every record carries `basis`: `full-text` or `abstract`. This governs what may be
extracted, and it goes in the output table.

Work in batches of 5–8. Full texts run 40,000–120,000 characters. Append each
batch to the CSV before starting the next, so an interruption costs one batch.

## CIMO does not apply to every paper

CIMO presupposes an intervention. A survey asking students how they feel about
ChatGPT has no intervention, no mechanism, and no outcome in the CIMO sense —
it has perceptions. Forcing it into CIMO produces fabricated design propositions.

So `cimo_applicable` gates the other CIMO fields. Answer it first. When it is
`no`, leave intervention, mechanism, and outcome blank and move on.

The proportion of `no` is itself a headline finding. A literature that is
overwhelmingly perception studies cannot support prescriptive claims about what
works, and saying so is a genuine contribution — it is the gap that justifies
future experimental work.

## Mechanism is the hard field, and the honest one

The M in CIMO is the element reviewers most often fake. Papers rarely state a
generative mechanism outright; Denyer et al. expect the reviewer to reason it out
of the discussion section. That means:

- It cannot be extracted from an abstract. Leave it blank for abstract-only
  sources — every time, without exception.
- Where you do reason it from full text, record the paper's own explanatory
  language first, then your reading of it, and flag the row for review.
- Where a paper reports an effect but offers no explanation of why, say so. "No
  mechanism offered" is accurate and useful; an invented mechanism is neither.

A table where every row has a confident mechanism is a table where mechanisms
were invented. Expect many blanks and defend them.

## The rules that make the table usable

**Never fill a cell from a source that does not contain the answer.** Fields
marked `requires: full-text` stay empty for abstract-only items. Empty is a
finding — it names the PDFs the user still needs.

**"Not stated" and blank differ.** "Not stated" means you read the source and the
information is absent. Blank means you could not check. They support different
claims about the literature; keep them distinct.

**Extract the paper's claims, not their validity.** Extraction records a study's
own account of itself. Appraisal is a separate stage. A weak study's overstated
finding is recorded as its finding, and its weakness noted elsewhere.

**Quote-anchor interpretive fields.** For characteristics, mechanism, outcomes,
and findings, carry a short verbatim phrase alongside the value so any cell can
be traced without reopening the source.

**Flag uncertainty rather than resolving it silently.** A short list of genuinely
uncertain rows is useful. A uniformly confident table that should not be is not.

## Output

Write CSV. Ask where to save it; never write into the plugin directory. Columns:

```
key, cite, basis, <schema fields in framework order>, confidence, needs_review, notes
```

`key` is the Zotero item key — what makes a row traceable back to the library
months later. `basis` must never be dropped; a reviewer who cannot tell which
rows came from abstracts cannot judge the extraction.

Report progress after each batch: done, remaining, rows flagged.

## Synthesis, once extraction is done

**TCCM** yields the characterisation: which theories dominate and which are
absent, which contexts are over- and under-studied, which constructs recur, which
methods prevail. Gaps here are the research agenda.

**CIMO** yields design propositions, but only from rows where `cimo_applicable`
is `yes` and a mechanism is genuinely supported. State each as:

> In [context], [intervention] invokes [mechanism], delivering [outcome].
> Supported by: [sources]. Contradicted by: [sources].

Propose one only where more than one study supports it, or say plainly that it
rests on a single study. A design proposition built on one paper with an inferred
mechanism is a hypothesis, and should be labelled as one.

## Closing summary

Say honestly:

- How many rows came from full text versus abstract
- How many papers were CIMO-applicable
- Which fields are substantially empty, and why
- What the table can and cannot support
- Which specific PDFs would most improve it
