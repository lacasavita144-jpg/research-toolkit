---
name: draft-review
description: Read a draft against the sources it cites and push back — unsupported claims, evidence thinner than the argument built on it, sources cited but never engaged, and citations that do not match the library. Use when the user wants feedback on a chapter, article, or section, or wants to check whether their argument holds.
argument-hint: [path to draft]
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py:*) Read Write Glob Grep
---

# Reading a draft against its sources

The point of this review is friction. Praise that is not load-bearing wastes the
user's time; they are going to submit this to people who will not be gentle.

## Setup

Read the whole draft before commenting on any part of it. An argument that looks
unsupported in section 2 is often established in section 4, and flagging it
anyway destroys your credibility for the rest of the review.

Then pull the library so citations can be checked against something real:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py sources --format md
python3 ${CLAUDE_PLUGIN_ROOT}/lib/zotero.py annotations --search "AuthorName"
```

Ask what stage the draft is at. A first draft and a resubmission need opposite
reviews: the first needs structural feedback and would be actively harmed by line
edits, the second needs precision and would be derailed by "reconsider the
framing."

## What to look for

**Claims carrying more weight than their evidence.** The core failure mode in
humanities and social-science writing is a hedged source supporting an unhedged
claim. If the source says "suggests" and the draft says "demonstrates," that is a
finding. Quote both.

**Citations that do not check out.** For each cited work, confirm it exists in the
library, and where highlights exist, confirm the passage actually says what the
draft claims. Report three cases separately, because they are different problems:
not in the library at all; in the library but the cited page does not support the
claim; supported but overstated.

**Decorative citation.** A source cited once in a list and never engaged. In a
literature review this is padding; where the source disagrees with the draft's
argument, it is worse — it looks like the objection was noticed and buried.

**Missing counterargument.** Check the library for sources that cut against the
draft's thesis. If they are in the library and absent from the draft, name them.
This is the single most common reason for a rejection the author saw coming.

**Structural drift.** Whether the argument promised in the introduction is the one
the conclusion delivers. Say which one is better — often the drifted argument is
the stronger one, and the fix is to rewrite the introduction, not the body.

## Reporting

Lead with the strongest objection, the one a hostile reviewer would open with.
Not the easiest to fix — the most damaging.

For each point: quote the draft, state the problem in one sentence, and say what
would fix it. Vague feedback like "this section needs work" is unusable; "this
paragraph asserts causation from three interviews; either soften to 'suggests' or
bring in the survey data from Chen 2020" is usable.

Separate the categories, because they cost different amounts to fix:

- **Argument** — needs rethinking
- **Evidence** — needs more or better sources
- **Citation** — needs checking or correcting
- **Prose** — needs editing

Say plainly if the draft is in good shape. An inflated problem list is as useless
as an empty one, and the user cannot tell which they are getting unless you are
willing to say both.

## What not to do

Do not rewrite the draft. Do not impose a style preference as though it were a
problem. Do not soften a real objection into a question — if the argument does
not hold, say that it does not hold, and say why.
