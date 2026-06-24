<p align="center">
  <picture>
    <source srcset="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/banner.en.svg" type="image/svg+xml">
    <img src="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/banner.png" alt="Bookwright — spec-driven authoring toolkit for novels, essays, and memoirs" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/jmorenobl/bookwright/actions/workflows/tests.yml"><img src="https://github.com/jmorenobl/bookwright/actions/workflows/tests.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/jmorenobl/bookwright/blob/main/CHANGELOG.md"><img src="https://img.shields.io/badge/version-0.5.9-6f42c1" alt="Version 0.5.9"></a>
  <a href="https://github.com/jmorenobl/bookwright/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-EUPL--1.2-blue" alt="License: EUPL-1.2"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-3776ab?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/coverage-%E2%89%A580%25-2ea44f" alt="Coverage ≥80%">
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white" alt="Linted with Ruff"></a>
  <img src="https://img.shields.io/badge/types-mypy%20strict-2a6db2" alt="Typed with mypy --strict">
  <a href="https://github.com/github/spec-kit"><img src="https://img.shields.io/badge/built%20with-Spec%20Kit-0b7285" alt="Built with Spec Kit"></a>
</p>

<p align="center">
  <b>Spec-driven authoring toolkit for novels, essays, and memoirs.</b><br>
  <i><a href="https://github.com/jmorenobl/bookwright/blob/main/README.es.md">Léeme en español</a></i>
</p>

Bookwright applies the Spec-Driven Development pattern to long-form
writing: you distill your ideas into a handful of canonical documents
(constitution, bible, outline, scenes) and let an AI agent write from
*them*, not from a free-form chat. Your book lives in plain text,
versioned in git, fully auditable, and outlives the toolkit.

**Why?** Because it warns you that your character has blue eyes in
chapter 3 and green eyes in chapter 12 — before your reader does.
Bookwright derives a knowledge graph from your work and validates
continuity (characters, settings, chronology, focalization)
deterministically.

> Status: **v0.5.9** — usable for researching, structuring, drafting and
> validating continuity. It researches with provenance, ingests the
> narrative structure (units, functions and sequences) and types it
> against the Propp and Greimas vocabularies, now flagging any unrecognized
> term with a non-fatal warning instead of typing it in silence. Validation
> is now robust: a
> validator reports `not-evaluated(reason)` instead of a misleading clean
> pass when it has nothing to look at. Change-by-change detail in
> the [CHANGELOG](https://github.com/jmorenobl/bookwright/blob/main/CHANGELOG.md).

---

## How you use it, in one sentence

Bookwright is **a CLI plus a set of skills for your agent**. That defines
*where* you type each thing, and it's the idea worth being clear on before
you start:

| When | Where | What |
| --- | --- | --- |
| **Once, at the start** | in your **terminal** | `bookwright init` |
| **95% of the time** | inside your **agent** (Claude Code, etc.) | you invoke skills: `/bookwright-constitution`, `/bookwright-bible`, … |
| **Now and then** | in your **terminal** | `bookwright graph build` · `bookwright validate` · `bookwright status` |

Skills are invoked **inside the agent**, by typing `/bookwright-<command>`
in the prompt. Whatever you type after the command reaches the skill as its
input (a reference to a file, pasted text, or the prior conversation).

---

## Installation

The PyPI package is `bookwright-cli`; the command it installs is `bookwright`.

```bash
uv tool install bookwright-cli   # with uv (recommended)
pipx install bookwright-cli      # or with pipx
bookwright version
```

Want to try it once without installing anything?

```bash
uvx --from bookwright-cli bookwright version
```

Straight from the repository (latest `main`):

```bash
uv tool install "git+https://github.com/jmorenobl/bookwright"
# or:  pipx install "git+https://github.com/jmorenobl/bookwright"
```

To work on the toolkit itself, clone the repo and sync the environment:

```bash
git clone https://github.com/jmorenobl/bookwright && cd bookwright
uv sync
uv run bookwright --help
```

---

## Quickstart: your first validated scene

### 1 · Create the project · `[in your terminal]`

```bash
bookwright init my-novel --integration claude
cd my-novel
```

This generates the structure (`bible/`, `outline/`, `manuscript/`), the
`manifest.toml`, and materializes the Bookwright skills in `.claude/skills/`.

Dump your idea into a free-form Markdown, with no required format — the
premise, the characters you already know, the tone:

```bash
echo "A pilgrim abandons the Camino de Santiago at stage 17..." > idea.md
```

### 2 · Distill your idea with the skills · `[in your agent]`

Open the project in Claude Code and invoke the first skill. **This is typed
in the agent's prompt, not in the terminal:**

```
/bookwright-constitution read idea.md and distill the constitution
```

The skill reads your brief, drafts the artifact, and marks with
`[PENDING: …?]` what your material does not yet decide — without inventing
canon. A typical session:

```
You  ▸ /bookwright-constitution read idea.md and distill the constitution

Claude ▸ I've read idea.md and drafted the constitution in
         bible/constitution.md. Summary:
           · Voice: close third person, focused on the pilgrim
           · Pact with the reader: psychological realism, no supernatural twists
           · Red lines: don't resolve the conflict with coincidences
         I've left 2 pending items I need you to decide:
           · [PENDING: what year does it take place?]
           · [PENDING: does the narrator know the ending from the start?]
```

You resolve the pending items whenever you like (by editing the `.md` or
re-invoking the skill) and continue with the rest of the pipeline, **in
order**:

```
/bookwright-bible      ← characters, settings, chronology, relationships
/bookwright-outline    ← arcs and act/chapter structure
/bookwright-scenes     ← breakdown into concrete scenes
/bookwright-draft      ← draft the prose of ONE scene
```

> These five are the main path. There are other support skills
> (`/bookwright-synopsis`, `/bookwright-clarify` to list open questions,
> `/bookwright-checklist` to check whether an artifact is complete,
> `/bookwright-analyze`, `/bookwright-continuity`, `/bookwright-research`,
> `/bookwright-verify`) that you'll use when you need them.

### 3 · Build and validate · `[in your terminal]`

```bash
bookwright graph build      # derives the GOLEM graph → bible/graph.ttl
bookwright validate         # exit 0 if there are no continuity errors
```

---

## The loop, not the staircase

That five-step order is only your **first pass**. Writing isn't linear:
researching a scene you discover a fact that changes a character, you
rethink the structure mid-draft, a late decision contradicts something you
took as settled. Bookwright is built for that back-and-forth, not for a
single descent down a staircase.

<p align="center">
  <picture>
    <source srcset="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/loop.svg" type="image/svg+xml">
    <img src="https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/loop.png" alt="The writer's loop: idea → scaffolding → distill → build and validate → edit, and back to the start" width="100%">
  </picture>
</p>

From the first pass onward, you work in a loop:

- **You discover something that changes the canon** (while researching, or
  just thinking) → you re-invoke the affected skill (`/bookwright-bible`,
  `/bookwright-outline`…). The generative skills **update in place**: they
  respect your prose and the pending items you've already resolved, and
  only fill in what's still open. They don't rewrite what you already
  decided.
- **You rethink the structure** → you go back to `/bookwright-outline`, and
  `/bookwright-analyze` points out what was left dangling across
  constitution, bible, outline and scenes (**pre-draft** consistency).
- **You already have prose and want to know what you broke** →
  `bookwright validate` (deterministic check over the graph) and
  `/bookwright-continuity` (the manuscript against the bible: compliance,
  arcs, chronology, **post-draft**).
- **For fact-based work**, research is its own sub-loop:
  `/bookwright-research` documents findings with provenance and marks which
  ones are *anchors* that constrain the fiction; `/bookwright-verify`
  checks the already-written prose against those anchors (anachronisms,
  procedural errors).
- **Forgot where you were?** `bookwright focus set` pins your current
  objective and `bookwright status` derives the state and the next step.

The engine behind all of this is the `[PENDING]` protocol: you leave a
marked gap, keep moving, and resolve it once the material is ripe. An
unanswered `[PENDING]` is treated as *undecided*, not as an answer — so a
voice declaration still left as `[PENDING: …]` stays invisible to the
continuity checks until you actually decide it, never a false alarm.
`/bookwright-clarify` lists the project's open questions for you at any
time. **There is no "definitive" pass**: there's a manuscript and a graph
that converge iteration by iteration.

The full walkthrough is in the
[Tutorial](https://github.com/jmorenobl/bookwright/blob/main/docs/tutorial/index.md).

---

## Design principles

- **Plain text is the source of truth.** Manuscript, bible, constitution
  and graph are Markdown, TOML or Turtle (RDF). Human-auditable,
  git-diffable, portable.
- **Batch, not conversational.** You consolidate the input; the skill
  distills it into a versionable artifact. You iterate on the *documents*,
  not the chat. The agent is not a sentence-by-sentence co-writer.
- **Agent-agnostic.** Skills are materialized as portable
  [Agent Skills](https://agentskills.io). Bookwright ships two integrations
  (`claude`, `generic`); agents like Codex, Cursor or Copilot consume the
  `generic` output directly.
- **GOLEM underneath.** The narrative graph uses the
  [GOLEM ontology](https://github.com/GOLEM-lab/golem-ontology) serialized
  in Turtle. You don't need to touch RDF to use Bookwright.

---

## Roadmap and out of scope

Bookwright already covers research with provenance, context orchestration
(authored focus and derived state with a next step) and ingestion of the
narrative structure: units, functions and sequences, with optional typing
against the Propp and Greimas vocabularies and a narrative-continuity
validator. The durable intent across versions lives in
[bookwright-roadmap.md](https://github.com/jmorenobl/bookwright/blob/main/bookwright-roadmap.md).

**Demand-pulled horizon (no version assigned)**, activated only by a
concrete trigger, never as speculative plumbing: **vector search**
(activated by a real multi-book / series corpus or a measured
structural-recall failure) and **export** to EPUB / PDF / print (activated
once the end-to-end flow is proven on a real book).

**Cancelled (owner's decision), don't ask for it:** genre presets /
template packages; the `Grafeo` / `GrafeoIndexer` engine; integrations
beyond `claude` and `generic`; the extension system.

---

## Project documents

> **Note:** the project documentation — the documentation site and the design
> spec linked below — is currently available **in Spanish only**. This README is
> the English-language entry point; the rest of the docs have not been
> translated yet.

- **[Documentation site](https://github.com/jmorenobl/bookwright/blob/main/docs/index.md)** — full user guide
  (getting started, commands, validation, extending, FAQ).
- **[bookwright-design.md](https://github.com/jmorenobl/bookwright/blob/main/bookwright-design.md)** — the complete
  design specification.
- **[bookwright-roadmap.md](https://github.com/jmorenobl/bookwright/blob/main/bookwright-roadmap.md)** — the durable
  intent across versions.
- **[CONTRIBUTING.md](https://github.com/jmorenobl/bookwright/blob/main/CONTRIBUTING.md)** — install, quality gates and
  how to extend the toolkit (new integration, validator, vocabulary).
- **[CHANGELOG.md](https://github.com/jmorenobl/bookwright/blob/main/CHANGELOG.md)** — change history.

## License

[EUPL-1.2](https://github.com/jmorenobl/bookwright/blob/main/LICENSE) (European Union Public Licence v. 1.2; the `LICENSE` file carries the official Spanish and English texts). See [NOTICE](https://github.com/jmorenobl/bookwright/blob/main/NOTICE) for attribution.

This license covers the **bookwright software only**. The content you
author with it — story bibles, outlines, manuscripts, and the derived
knowledge graphs — remains entirely yours.
