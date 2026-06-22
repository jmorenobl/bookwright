---
name: bookwright-release
description: >-
  Cut a Bookwright patch release after an iteration is implemented and green.
  Use when the user asks to release / cortar / publicar an iteration, bump the
  version, "haz la release", "corta el patch vX.Y.Z", "release iteration NNN",
  or merge a finished iteration to main with its release metadata. Drives the
  fixed sequence: verify gates → merge to main → bump __version__ → CHANGELOG →
  CLAUDE.md → design (if a concept was wired) → release commit → annotated tag.
metadata:
  author: bookwright
  audience: maintainers
---

# Cut a Bookwright patch release

A finished iteration always ships the same way: dump the new version, update
the same handful of plain-text files, commit, tag, and merge to `main`. This
skill is the canonical playbook. It is mostly mechanical, with three editorial
steps (the CHANGELOG entry, the CLAUDE.md prose, and the optional design note)
that need your judgement — write real prose, do not template-fill.

## When this runs

The iteration `NNN-<short-name>` is **fully implemented, tested, and green** on
its branch (the `/speckit-implement` flow is done and `/speckit-analyze` reports
no issues). Releases are **not** part of the numbered-iteration flow — they land
as a direct `Release vX.Y.Z` commit on `main`, like the `docs:`/`ci:` commits.

Do **not** invoke this to write code or fix failing tests. If the gates are red,
stop and report — there is nothing to release.

## Inputs to resolve first

1. **Iteration number + branch.** Usually the current branch `NNN-<short-name>`.
2. **Target version.** Read the current `__version__` from
   `src/bookwright/__init__.py`, then take the mapping from
   `bookwright-implementation-plan.md` / the iterations table in `CLAUDE.md`
   (e.g. 024→`v0.3.1`, 025→`v0.3.2`, 026→`v0.3.3`, 027→`v0.3.4`). The v0.3.x
   track ships one **patch** per iteration. If the next version is not obvious
   from the plan, ask.
3. **One-line iteration title** (from the table, e.g. "index objects (G16)").

## Procedure

### 1. Verify the gates are green (blocking)

```
uv run ruff check && uv run ruff format --check && uv run mypy --strict && uv run pytest
```

All four must pass (coverage ≥ 80 %, single-sourced — never pass
`--cov-fail-under`). If anything fails, stop and report; do not release.

### 2. Merge the iteration branch to `main`

Standardize on a **`--no-ff` merge commit** (the dominant historical pattern:
iterations 011, 020, 022, 023, 024). Some past patches landed linearly (025) —
prefer the merge commit going forward for a uniform, bisectable history.

```
git checkout main
git merge --no-ff NNN-<short-name> -m "Merge iteration NNN: <title> (vX.Y.Z)"
```

If the iteration is already on `main`, skip this step.

### 3. Bump the version

Edit `src/bookwright/__init__.py`: `__version__ = "X.Y.Z"`. This is the **single**
source — `hatchling` reads it via `[tool.hatch.version]`. No other file holds the
version. (The `resources/schemas/golem-1.1/VERSION` file is the ontology schema
version, **not** the package version — leave it alone.)

### 4. CHANGELOG.md entry (editorial)

Insert a new `## [X.Y.Z] — YYYY-MM-DD` section at the top, above the previous
release. Match the house style of the prior entries:

- A lead paragraph naming the patch ("Nth patch of the **v0.3.x hardening
  track** (iteration NNN)"), what concept/behaviour it wires, and the
  invariants it preserves — typically the line "No new CLI surface, no new
  runtime dependency, no ontology change … — pure hardening" **when true**.
- `### Added` and `### Changed` subsections with concrete file paths and the
  observable delta (e.g. deferral registry `N → N-1`, parity reachable set
  `M → M+1`).
- No link-reference footnotes — the file does not use them.

### 5. CLAUDE.md (editorial)

Three edits, all in English:

- The iterations **table**: flip the row's status from `⏳ planned` to
  `✅ merged`.
- The one-line prose under "## Iterations" ("… 026 is merged (v0.3.3); 027 is
  planned …").
- The **status paragraph** in the milestone overview (the "v0.3.x hardening
  track" paragraph): record this iteration as wired/merged with its version and
  point "Next" at the following iteration.

Leave the `<!-- SPECKIT START -->` managed block alone — `/speckit-specify` of
the next iteration refreshes it.

### 6. bookwright-design.md — only if the iteration wired a concept (editorial)

If the iteration moved a GOLEM concept from orphan to ingested (the v0.3.x
hardening pattern), record it **in Spanish** (the design doc is Spanish):

- Add/flip a `### 7.x Ingesta de … (GNN) — wired en iteración NNN (vX.Y.Z)`
  note, mirroring § 7.2 (locations) and § 7.3 (objects).
- Add the directory to the `bible/` project-tree diagram (§ 7.1 area).
- Never reopen a § 16 axiom and never add a class/property to the frozen
  ontology (Principle X) — the class already exists; you are only documenting
  the new ingestion path.

If the iteration touched no canonical design (e.g. a pure JSON-envelope
cleanup), skip this file.

### 7. README.md + README.es.md — version badge + status line (editorial)

Both READMEs ship together (English + Spanish, mirror images) and carry the
version in **two** places each: the shields.io **version badge**
(`badge/version-X.Y.Z-…` + the `alt="Version X.Y.Z"` / `alt="Versión X.Y.Z"`
text) and the **`> Status:` / `> Estado:`** blockquote near the top. Bump both:

- Update all four references (badge URL + alt text in each file) to the new
  `X.Y.Z`.
- Refresh the status-line prose **only when the release changes a user-visible
  capability** (a new verb, a changed validation/output behaviour) — keep
  README.md in English and README.es.md in Spanish, as mirror translations. A
  pure-internal patch (no observable delta) bumps the version numbers and leaves
  the prose as-is.

These are easy to forget (the badge lagged a release before this step existed)
— treat them as **always** part of the release, like CLAUDE.md.

### 8. Re-verify

```
uv run bookwright version    # must print the new X.Y.Z
uv run pytest -q             # still green
```

### 9. Release commit on `main`

```
git add -A
git commit -m "Release vX.Y.Z: <title> (iteration NNN)" -m "<body>"
```

Body: one paragraph on what shipped + one paragraph on the release-metadata
changes (version bump, CHANGELOG, deferral-registry delta, CLAUDE.md/design
updates). End with the project's `Co-Authored-By` trailer.

### 10. Annotated tag

```
git tag -a vX.Y.Z -m "Release vX.Y.Z: <title> (iteration NNN)"
```

### 11. Stop — do not push

Per project rule, **commit and tag only; never `git push` unless the user asks.**
Report the new commit, the tag, and how far `main` is ahead of `origin/main`,
and offer to push (`git push && git push --tags`).

## Files touched per release

| File | Always? | Kind |
|---|---|---|
| `src/bookwright/__init__.py` | yes | mechanical (1 line) |
| `CHANGELOG.md` | yes | editorial |
| `CLAUDE.md` | yes | editorial |
| `README.md` + `README.es.md` | yes | mechanical badge/status bump (+ editorial prose if a capability changed) |
| `bookwright-design.md` | only if a concept was wired / a design decision recorded | editorial |
| git tag `vX.Y.Z` | yes | mechanical |

## Guardrails

- Never invent a version — derive it from the plan/table; ask if ambiguous.
- Never `git push` without an explicit request.
- Never bump the version anywhere but `src/bookwright/__init__.py`.
- If gates are red, abort the release.
- This is metadata only — it does not add features. If you find yourself editing
  `src/` logic, you are doing iteration work, not a release.
