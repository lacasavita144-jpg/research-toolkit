---
name: extract
description: Extract TCCM (theory, context, characteristics, methodology) and CIMO (context, intervention, mechanism, outcome) data from a corpus of papers into a CSV table, reading Zotero full texts where they exist and abstracts otherwise. Use for systematic review data extraction, evidence tables, or building design propositions.
argument-hint: [collection or tag]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write Edit
---

# TCCM + CIMO extraction

Seven fields, defined in `${CLAUDE_SKILL_DIR}/schema.json`. Read it first — it is
meant to be edited.

## Running it

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py queue --tag "SLR corpus"
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py text --tag "SLR corpus" --limit 8
```

Show the user the full-text and abstract counts, confirm the schema, then work in
batches of 5–8. Append each batch to the CSV before starting the next.

Every record carries `basis`: `full-text` or `abstract`. It goes in the table and
governs what may be filled in.

## Four rules

**Blank beats guessed.** `mechanism` needs full text — leave it empty for the rest.
Empty cells name the PDFs still needed.

**"None" is a real answer.** Most papers name no theory. Many are not intervention
studies. Record that plainly instead of stretching a field to fit.

**Mechanism is reasoned, not read.** It is the field reviewers most often fabricate.
Record the paper's own explanation where it gives one, flag the row where you went
beyond it, and write "none offered" where the paper explains nothing.

**Record claims, not their validity.** Appraisal is a separate stage.

## Output

CSV, saved where the user asks — never in the plugin directory.

```
key, cite, basis, theory, context, characteristics, methodology,
intervention, mechanism, outcome, needs_review
```

Report after each batch: done, remaining, rows flagged.

## Afterwards

**TCCM** gives the characterisation — which theories, contexts, and methods
dominate, and which are missing. The gaps are the research agenda.

**CIMO** gives design propositions, but only from papers with a real intervention
and a supported mechanism:

> In [context], [intervention] invokes [mechanism], delivering [outcome].

Propose one only where more than one study supports it. On a single study, call it
a hypothesis.

Close by saying how many rows came from full text, how many papers had no
intervention, and what the table cannot yet support.
