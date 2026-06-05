<p align="center">
  <img src="assets/banner.en.svg" alt="Bookwright — Spec-driven authoring toolkit for novels, essays, and memoirs" width="100%">
</p>

<p align="center">
  <a href="https://github.com/jmorenobl/bookwright/actions/workflows/tests.yml"><img src="https://github.com/jmorenobl/bookwright/actions/workflows/tests.yml/badge.svg" alt="CI"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-0.2.0-6f42c1" alt="Version 0.2.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="License: Apache-2.0"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-3776ab?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/coverage-%E2%89%A580%25-2ea44f" alt="Coverage ≥80%">
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white" alt="Linted with Ruff"></a>
  <img src="https://img.shields.io/badge/types-mypy%20strict-2a6db2" alt="Typed with mypy --strict">
  <a href="https://github.com/github/spec-kit"><img src="https://img.shields.io/badge/built%20with-Spec%20Kit-0b7285" alt="Built with Spec Kit"></a>
</p>

<p align="center">
  <b>Spec-driven authoring toolkit for novels, essays, and memoirs.</b><br>
  <i><a href="README.md">Léeme en español</a></i>
</p>

Bookwright applies Spec-Driven Development to long-form writing: you distill
your ideas into a small set of canonical documents (constitution, bible,
outline, scenes) and let an AI agent write from *them*, not from a free-form
chat. Your book lives in plain text, versioned in git, fully auditable, and
outlives the toolkit.

> **Status: v0.2.0.** The v0.1.0 toolkit (iterations 1–11) and the M4
> research & verification milestone (iterations 12–18) are both on `main`.

The canonical README and the full documentation are in Spanish (the language of
the design corpus). The English-facing surface is the code, the CLI, and the
constitution.

- **[README.md](README.md)** — canonical README (Spanish): qué es, instalación,
  quickstart de 5 minutos, enlaces a la documentación.
- **[Documentation site](docs/index.md)** — getting started, per-command
  reference, validation, extending, FAQ (Spanish).
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — install, quality gates, and how to
  add a new integration / validator / vocabulary.
- **[CHANGELOG.md](CHANGELOG.md)** — release history.

## Quickstart

Scaffold a project, then distill your idea with the authoring skills — you don't
fill the canonical documents by hand: each skill reads your brief (e.g.
`idea.md`) and asks only for what's missing.

```bash
bookwright init my-novel --integration claude   # scaffolding + Agent Skills
cd my-novel
```

Open the project in your agent and run the skills in order:

```
/bookwright-constitution read idea.md and distill the constitution
/bookwright-bible        ← characters, settings, timeline
/bookwright-outline      ← arcs and act/chapter structure
/bookwright-scenes       ← break chapters into scenes
/bookwright-draft        ← draft the prose of one scene
```

For fact-based work (e.g. historical fiction), the optional research loop
records sources, findings and anchors, then checks the prose against them:

```
/bookwright-research <topic>   ← document findings with full provenance
/bookwright-verify             ← check the drafted prose against the anchors
```

Then build and validate from the CLI:

```bash
bookwright graph build                            # → bible/graph.ttl
bookwright validate                               # exit 0 when there are no errors
```

To work on the toolkit itself, sync the project environment:

```bash
uv sync
uv run bookwright --help
```

See [docs/getting-started.md](docs/getting-started.md) for the full 5-minute
walkthrough.

## License

[Apache-2.0](LICENSE). See [NOTICE](NOTICE) for attribution.

This license covers the **bookwright software only**. The content you author
with it — story bibles, outlines, manuscripts, and the derived knowledge
graphs — remains entirely yours.
