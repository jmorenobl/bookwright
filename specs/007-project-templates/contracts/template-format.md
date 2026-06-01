# Contract: Cross-Cutting Template Format

The authoring rules every template (skeleton + mold) MUST satisfy, independent of
the parser/walker contracts. Verified by
`tests/resources/test_authoring_guidance.py` and `test_no_stub_sentinels.py`.

## F1. Plain-Markdown legibility

Each file reads as clean Markdown without a renderer (FR-017, Acceptance 1.2).
No unresolved scaffolding syntax, no half-open HTML comment, no raw template
directive in a `.md`/`.tmpl` file (only `.j2` files carry Jinja2).

## F2. Language split (Clarification Q1)

- **Spanish**: all human-facing scaffolding prose — section headings, body
  labels, HTML-comment guidance, `[PENDING]` *questions*, and the authored
  `README.md.j2` guidance prose.
- **English**: frontmatter **keys**, the literal `[PENDING]` token, and the
  verify-only `manifest.template.toml` comments.

## F3. HTML-comment guidance + worked example (FR-018)

- Every authored template includes ≥1 `<!-- … -->` block carrying instructions
  for the human author or AI agent; these MUST NOT render as visible body prose.
- Every template includes a short **worked example** of the expected shape,
  placed **inside** an HTML comment so it never renders, never indexes, never
  trips the sentinel sweep (F5).
- For `timeline.md` / `relationships.md`, the example `events:` / `relationships:`
  entries live in HTML comments while the shipped frontmatter lists stay **empty**
  (ties F3 to the frontmatter contract C4).

## F4. `[PENDING: <question>]` prompts (FR-019)

Sections the agent must populate from a narrative brief use
`[PENDING: <pregunta>]` placeholders phrased as the question to answer. These
appear only in **prose** or in **string-typed** frontmatter values — never in
an int/list-typed frontmatter value (would violate C3). In a string-typed value
the prompt MUST be **quoted** (`name: "[PENDING: …]"`); bare brackets parse as a
YAML list (C3). The token stays English; the question is Spanish.

## F5. No stub / scaffolding sentinels (FR-022)

No authored or stamped file retains `Placeholder — iteration 7 lands the full
template`, `{{TODO}}`, or any equivalent scaffolding marker. The sentinel sweep
runs over both `resources/project/` (and a freshly-stamped temp project) and
`resources/templates/`.

## F6. Originality + attribution (FR-021)

Template structure is *inspired by* the MIT `fiction-book-writing` preset but the
prose is **original Bookwright** adapted to GOLEM — no verbatim preset text.
`CHANGELOG.md` credits the preset (adaumann, MIT), states the redaction is
original (Apache-2.0) and adapted to GOLEM, and records the design § 6 layout
supersession.

## F7. Verification

- `test_authoring_guidance.py`: per authored template, assert ≥1 HTML-comment
  block, presence of `[PENDING:` in author-fill sections, valid YAML where a
  fence is present, and Spanish prose heuristics where applicable.
- `test_no_stub_sentinels.py`: assert F5 across both resource trees and a stamped
  temp project.
- CHANGELOG assertion (F6/SC-006) verifies the credit + supersession note exist.
