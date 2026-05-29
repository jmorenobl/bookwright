# Bookwright

**A spec-driven authoring toolkit for novels, essays, and memoirs.**

*[Leer en español](README.es.md)*

Bookwright applies the Spec-Driven Development pattern to long-form writing:
you distill your ideas into a small set of canonical documents
(constitution, bible, outline, scenes) and let an AI agent draft from
*those* — not from a freeform chat. Your book lives in plain text, version
controlled in git, fully auditable, and survives the toolkit.

> ### Status: pre-alpha
>
> Bookwright is **under active construction**. Iterations 1 and 2 of 11
> have landed on `main`; iteration 3 (integration architecture) is in
> flight. The authoring commands a writer actually uses
> (`/bookwright-constitution`, `/bookwright-bible`,
> `/bookwright-outline`, `/bookwright-draft`, …) ship in iterations 7–9.
>
> If you're a writer evaluating Bookwright today, **bookmark the
> repository and check back at v0.1**. If you're an early collaborator or
> AI agent developer, read on.

## How it will work (the writer's loop)

1. **Ideate freely** — talk to claude.ai, Gemini, ChatGPT, or your
   notebook. Dump the conversation or a brief into a Markdown file.
2. **Scaffold a project** — `bookwright init my-novel --integration claude`
   generates the directory layout, the canonical document templates, and
   installs Bookwright's *Agent Skills* into `.claude/skills/` so your
   agent can invoke them.
3. **Distill, in order** — open the project with Claude Code (or any
   [agentskills.io](https://agentskills.io)-compatible agent) and run:

   ```
   /bookwright-constitution   ← non-negotiable rules for the work
   /bookwright-bible          ← characters, settings, lore
   /bookwright-outline        ← act/chapter structure
   /bookwright-scenes         ← beat-by-beat breakdown
   /bookwright-draft          ← per-scene prose generation
   ```

   Each command takes unstructured input and produces a versionable
   Markdown / Turtle artifact. You iterate the *documents*, not the
   draft.

4. **Validate continuity** — `bookwright validate` runs consistency
   checks (temporal continuity, character presence, focalization,
   historical anchors) against the narrative graph derived from your
   bible and manuscript.

5. **Edit in your favorite editor** — Bookwright is not a text editor.
   Open the `.md` files in Obsidian, Scrivener, VS Code, vim. The
   toolkit hands the manuscript back to you in plain text.

## Design principles

- **Plain text is the source of truth.** Manuscript, bible,
  constitution, and the narrative graph are all Markdown, TOML, or
  Turtle (RDF). Auditable by humans, diffable in git, portable.
- **Agent-agnostic.** Bookwright targets Claude Code first, but the
  command layer is materialized as portable
  [Agent Skills](https://agentskills.io). v0 ships two integrations
  (`claude`, `generic`); Copilot, Gemini, and Cursor-native variants are
  on the roadmap.
- **Batch, not conversational.** You consolidate input; the command
  distills it. The agent is not a frase-a-frase co-writer.
- **GOLEM under the hood.** The narrative graph uses the published
  [GOLEM ontology](https://github.com/GOLEM-lab/golem-ontology)
  (characters, events, settings, relationships, narrative structure,
  inference provenance) serialized as Turtle.

## What works today

Only the toolchain shell is wired up. There is no `bookwright init` yet.

```bash
uv sync                          # install the project environment
uv run bookwright --help         # list available commands
uv run bookwright version        # CLI + schema version
uv run bookwright check          # verify the toolchain
```

Both `version` and `check` accept `--json` for agent consumption.

## Roadmap to v0

The 11-iteration plan lives in
[bookwright-implementation-plan.md](bookwright-implementation-plan.md).
Milestones:

| Milestone | Iterations | What it unlocks |
|---|---|---|
| **M0** — toolchain | 1–4 | `bookwright init`, project scaffolding |
| **M1** — graph | 5–6 | GOLEM domain model, `bookwright graph` commands |
| **M2** — authoring | 7–9 | Templates + the 10 source commands + Agent Skills materialization |
| **M3** — validation | 10–11 | Continuity checks, end-to-end fixtures, docs |

Out of v0 scope (do not request these for v0): genre presets (v0.2),
vector search (v0.3), additional integrations (v0.4), extension system
(v0.5), EPUB/PDF export (v1.0).

## Project documents

- **[bookwright-design.md](bookwright-design.md)** — the full design
  spec (Spanish, ~1.4k lines). Section numbering is load-bearing.
- **[bookwright-implementation-plan.md](bookwright-implementation-plan.md)**
  — the ordered iteration plan (Spanish).
- **[.specify/memory/constitution.md](.specify/memory/constitution.md)** —
  the ratified, binding principles for every PR.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — install, quality gates,
  pre-commit hooks for collaborators and AI agents working on the
  toolkit itself.

## License

To be decided before v0.1. Tracked in the design doc.
