# Bookwright

**Spec-driven authoring toolkit for novels, essays, and memoirs.**

Bookwright applies Spec-Driven Development to long-form writing: you distill
your ideas into a small set of canonical documents (constitution, bible,
outline, scenes) and let an AI agent write from *them*, not from a free-form
chat. Your book lives in plain text, versioned in git, fully auditable, and
outlives the toolkit.

> **Status: v0.1.0.** All eleven v0 iterations have landed on `main`.

The canonical README and the full documentation are in Spanish (the language of
the design corpus). The English-facing surface is the code, the CLI, and the
constitution.

- **[README.es.md](README.es.md)** — canonical README: qué es, instalación,
  quickstart de 5 minutos, enlaces a la documentación.
- **[Documentation site](docs/index.md)** — getting started, per-command
  reference, validation, extending, FAQ (Spanish).
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — install, quality gates, and how to
  add a new integration / validator / vocabulary.
- **[CHANGELOG.md](CHANGELOG.md)** — release history.

## Quickstart

```bash
uv sync
uv run bookwright --help
```

See [docs/getting-started.md](docs/getting-started.md) for the full 5-minute
walkthrough.

## License

[Apache-2.0](LICENSE).
