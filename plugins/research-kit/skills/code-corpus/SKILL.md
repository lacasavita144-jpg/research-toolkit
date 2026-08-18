---
name: code-corpus
description: Thematic coding and synthesis across a body of published literature — build or apply a codebook, track which sources carry which themes, surface disagreements, and assemble an evidence table. Use for literature reviews, thematic synthesis, "what does the literature say about X", or finding where sources contradict each other.
argument-hint: [collection or research question]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write Glob Grep
---

# Coding a literature corpus

This is thematic synthesis across published sources, not transcript coding. The
unit of analysis is a *claim in a paper*, and every code must be traceable back
to a specific source and page.

## Assembling the corpus

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py sources --collection "Lit review" --format md
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py annotations --collection "Lit review"
```

State the corpus boundary explicitly before coding: how many sources, drawn from
where, and what was excluded. A synthesis whose scope is unstated cannot be
checked by anyone, including the user later.

Where highlights exist, code those — they are already the passages the user found
salient. Where they do not, code from abstracts and say so, because an
abstract-level synthesis is a weaker claim than a full-text one and the write-up
must not blur the two.

## Building the codebook

Ask whether the user has an existing codebook. If they do, apply it as given and
report what does not fit rather than silently widening a code.

If they do not, work inductively:

1. Read across the corpus and propose 5–9 candidate codes. Fewer collapses real
   distinctions; more fragments the corpus into singletons.
2. Give each code a one-line definition and a boundary — what it excludes. The
   boundary is what makes a code usable by someone else.
3. Show the proposed codebook and get agreement **before** coding everything.
   Recoding a corpus is expensive; disagreeing about a definition is cheap.

## The evidence table

Output a table with one row per source, and mark which codes it carries:

| Source | Method | Code A | Code B | Code C |
|---|---|---|---|---|
| Ahmed 2019 | ethnographic | ● p.44 | — | ● p.51 |

Include the method column. In social science and humanities, whether a claim
comes from ethnography, survey, close reading, or archival work substantially
changes what it can support, and a synthesis that flattens method is misleading.

## What synthesis actually requires

Counting how many sources carry a code is the weakest possible finding. Frequency
reflects what gets published and what the user happened to collect — not what is
true. Say so plainly if asked to rank themes by count.

The findings worth reporting are:

- **Disagreement.** Two sources making incompatible claims is the most valuable
  thing in a corpus. Name both, quote both, and state what would settle it.
- **Method-patterned results.** A theme that appears only in qualitative work, or
  only post-2015, or only in one national context, is a finding about the
  literature itself.
- **Absence.** A code you expected and did not find. Flag it as a possible gap,
  but distinguish "the literature does not address this" from "this corpus does
  not address this" — usually you can only support the second.
- **Singletons.** A claim only one source makes, presented as settled elsewhere.

## Honesty constraints

Never invent a source, a page number, or a quotation. If a claim cannot be tied
to a specific source in the corpus, it does not go in the synthesis.

If the corpus is too small or too narrow to support the question being asked, say
that first and continue with what it does support. Ten sources on one country
cannot answer a comparative question, and the write-up should say which question
it is actually answering.
