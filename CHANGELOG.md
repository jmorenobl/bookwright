# Changelog

All notable changes to Bookwright are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow semantic versioning.

## [Unreleased]

### Added — Iteration 7: Bible / Outline / Constitution templates

- Authored the real narrative skeleton stamped by `bookwright init`: the
  `bible/` documents (constitution, timeline, relationships, themes, glossary,
  research, subplots, POV structure) and the `outline/` documents (synopsis,
  structure, arcs, scenes), replacing the iteration-4 placeholder stubs. Each is
  Spanish literary-technical prose with HTML-comment craft guidance, worked
  examples inside comments, and `[PENDING: …]` prompts in author-fill sections.
- Authored the re-instanceable molds under `resources/templates/`
  (`character`, `setting`, `location`, `chapter`, `scene`) for the upcoming
  authoring commands (iterations 8–9). The `character` and `setting` molds carry
  frontmatter aligned exactly to the iteration-6 GOLEM mapper's recognized keys,
  so a fresh project indexes with zero skips and zero `unknown_keys`.
- Added a `tests/resources/` format / round-trip validation suite (sentinel
  sweep, frontmatter-contract round-trip via `map_bible`, filled-instance →
  GOLEM entity, Jinja2 `StrictUndefined` render, mold-structure and
  authoring-guidance lint).

### Attribution

- The template **structure** (the document inventory: short + long synopsis,
  themes with a motif registry, locations with sensory anchors, glossary,
  research, subplots, POV structure) is inspired by the
  [`fiction-book-writing`](https://github.com/adaumann/fiction-book-writing)
  preset by **adaumann** (MIT-licensed), whose license permits structural reuse
  with attribution. Bookwright's redaction is **original** prose under
  **Apache-2.0**, rewritten in Spanish and adapted to the **GOLEM** narrative
  model — no verbatim preset text is included.

### Changed — supersedes design § 6

- This iteration **supersedes** `bookwright-design.md` § 6's single unified
  `resources/templates/*.tmpl` layout with a four-layer `resolve_template()`
  resolver, in favor of a **lifecycle split**: stamped-once skeleton singletons
  live under `resources/project/` (rendered/byte-copied by the iteration-4
  walker) and re-instanceable molds live under `resources/templates/` (stamped
  many times by commands). The § 6 resolver only ever existed to serve presets
  (v0.2) and extensions (v0.5), which are out of v0 scope; building it now would
  be forbidden plumbing. § 6 is structural guidance, not a § 16 axiom, so the
  divergence is recorded here rather than litigated as a constitutional
  amendment.
