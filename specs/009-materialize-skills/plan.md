# Implementation Plan: Materialize commands as Agent Skills

**Branch**: `009-materialize-skills` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-materialize-skills/spec.md`

## Summary

Replace the iteration-3 placeholder-marker `setup()` with **real `SKILL.md`
materialization**. For each of the ten integration-agnostic source commands under
`bookwright.resources.commands/<name>.md`, materialize a per-skill directory
`<skills_dir>/<name>/SKILL.md` whose frontmatter carries an authoritative,
trigger-bearing `description` (from a `SKILL_DESCRIPTIONS` dict), `license`,
`metadata.author`/`metadata.version`, and whose body is the source body with every
`{ARGS}` token substituted by `$ARGUMENTS` and inline `bookwright … --json` calls
preserved. Cited `references/<file>.md` are copied into the skill's own
`references/`. Materialization is **idempotent per-`SKILL.md`** (existing files are
never overwritten), is constrained to the resolved `skills_dir` (project-root
contained), and **aborts that integration on any agentskills.io lint failure**
leaving no invalid `SKILL.md` on disk. Every directory/file it creates is **recorded
through `init`'s rollback ledger** (FR-019), so an aborted `init` removes all
materialized artifacts even when `skills_dir` pre-existed (no orphans).

**Technical approach**: a single shared helper
`bookwright.integrations.materialize.generate_skill_md(command_path, target_dir,
integration, *, ledger)` does the per-command work; the bilingual `SKILL_DESCRIPTIONS`
table lives in its own `descriptions.py`; `{ARGS}` substitution is a literal replace (the
only token). One **shared** `setup()` in `base.py` loops over the packaged command
roster calling the helper — the two v0 subclasses do **not** override it (their only
variation is already behind `resolve_skills_dir()` and the capability flags). No
`!`shell`` dynamic-context syntax is auto-emitted in v0 (capability stays declared,
materializer stays neutral). An ad-hoc agentskills.io linter (`lint_skill_md`, in its
own `lint.py`) gates each generated artifact.

**Transactional integrity**: the transactional-fs primitives (`BackupLedger`,
`mkdir_tracked`, `write_bytes_atomic`) are extracted from `commands/init/scaffold.py`
into a shared low-level module `bookwright/io/fs.py`, alongside a narrow `FileLedger`
**Protocol** (`record_new_file` / `record_new_directory` / `record_overwrite`, satisfied
structurally by `BackupLedger`) and a no-op `NullLedger`. `setup()` gains a keyword-only
`ledger: FileLedger | None = None` (defaulting to `NullLedger()` for standalone calls);
`scaffold.py` passes the live `BackupLedger`. The materializer creates every directory
and writes every file through these tracked helpers, so `init`'s rollback unwinds all
materialized artifacts — including the pre-existing-`skills_dir` case (FR-019). This
replaces the iteration-3 marker pre-record that `scaffold.py` did on the integration's
behalf. Dependency direction stays clean: `commands.init → io.fs` and
`integrations → io.fs`; `io` imports neither, so no cycle.

## Technical Context

**Language/Version**: Python 3.11+ (Constitution II / III).

**Primary Dependencies**: stdlib `string.Template`, `pathlib`, `importlib.resources`,
`shutil`; `pyyaml` (frontmatter read + write); existing `bookwright.io.frontmatter`;
new `bookwright.io.fs` (the transactional-fs layer extracted from `init/scaffold.py`).
No new runtime dependency (no constitutional amendment needed).

**Storage**: plain-text Markdown `SKILL.md` + copied `references/*.md` under the
integration's resolved `skills_dir`. Source commands shipped as packaged resources
(`bookwright.resources.commands`, already force-included in the wheel).

**Testing**: pytest. Unit tests for `generate_skill_md`, `lint_skill_md`,
`SKILL_DESCRIPTIONS`, token substitution, idempotency, reference copying, containment.
E2E: run materialization (and `bookwright init`) into `tmp_path`, assert every
generated `SKILL.md` passes the ad-hoc linter.

**Target Platform**: cross-platform CLI (darwin/linux CI).

**Project Type**: single-project CLI (src-layout, Constitution III).

**Performance Goals**: N/A (materializes ten small files once per `init`).

**Constraints**: each `SKILL.md` body within the ~5000-token Tier-2 budget;
`description` < 1024 chars; `name` == parent directory; valid YAML frontmatter;
writes never escape `skills_dir` (⊆ project root).

**Scale/Scope**: 10 source commands, 6 reference files, 2 v0 integrations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Plain text as source of truth | Output is Markdown `SKILL.md` + Markdown `references/`. No binary store. | ✅ PASS |
| II. Modern Python stack | Only stdlib + already-declared `pyyaml`/`jinja2` reused. No new dependency. | ✅ PASS |
| III. src-layout | Code under `src/bookwright/integrations/`; tests under `tests/`. | ✅ PASS |
| IV. Modular command surface | New concerns split by responsibility into `materialize.py`, `lint.py`, `descriptions.py`; the transactional-fs layer is extracted from the `scaffold.py` grab-bag into `io/fs.py`; `base.py` stays the lean contract. Every module well under 500 lines (decompose *before* the cap). | ✅ PASS |
| V. Plugin-based integrations | Materialization is the shared `generate_skill_md` helper; the single shared `setup()` is the plugin hook; subclasses vary only via `resolve_skills_dir`/flags. The integration receives rollback support through the narrow `FileLedger` **Protocol** (not the concrete `BackupLedger`), so it stays decoupled from `init` internals. No `AGENT_CONFIG` dispatcher. | ✅ PASS |
| VI. Agent Skills only | Emits exactly one `SKILL.md` per command under `skills_dir`; never writes to `commands/`. | ✅ PASS |
| VII. agentskills.io compliance | `lint_skill_md` enforces name==dir, description<1024, body≤Tier-2 budget, valid YAML; fails loud (abort, no file left). | ✅ PASS |
| VIII. Test discipline (≥80%) | Unit + E2E suites added; existing `test_setup_stub.py` rewritten to the materialization contract. | ✅ PASS |
| IX. JSON-over-stdout | No CLI output change here; materialized bodies call `bookwright … --json` (FR-009). | ✅ PASS |
| X. Design axioms | No shell scripts emitted; no `.bookwright/scripts/` wrappers; Agent Skills only; generic default `.agents/skills/`. | ✅ PASS |

**Scope discipline**: no preset plumbing, no Grafeo, no third integration, no
dynamic-context auto-injection (deferred). The lint check is the minimum needed for
VII; the full validation system stays in iteration 11. The `io/fs.py` extraction and
`FileLedger` Protocol are a **refactor in service of FR-019 correctness** (transactional
rollback over a pre-existing `skills_dir`), not speculative generality — they remove the
iteration-3 marker workaround rather than add new surface. **No violations — Complexity
Tracking left empty.**

## Project Structure

### Documentation (this feature)

```text
specs/009-materialize-skills/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── generate_skill_md.md   # shared materializer contract
│   └── lint_skill_md.md       # ad-hoc agentskills.io linter contract
└── tasks.md             # /speckit-tasks output (NOT created here)
```

### Source Code (repository root)

```text
src/bookwright/io/
└── fs.py                # NEW (extracted from init/scaffold.py) — FileLedger Protocol +
                         #   NullLedger + BackupLedger + mkdir_tracked + write_bytes_atomic.
                         #   Shared transactional-fs layer; imports only stdlib + io.errors.

src/bookwright/integrations/
├── base.py              # SkillsIntegration contract + ONE shared setup(*, ledger=None);
│                        #   no SKILL_DESCRIPTIONS / generate_skill_md here
├── materialize.py       # NEW — generate_skill_md(*, ledger) + iter_command_sources (PUBLIC:
│                        #   imported by base.py → cross-module ⇒ no leading underscore) +
│                        #   _transform_body + _render_frontmatter + _copy_references (private);
│                        #   creates dirs/writes files via io.fs tracked helpers (FR-019)
├── lint.py              # NEW — lint_skill_md() ad-hoc agentskills.io linter + approx_tokens()
├── descriptions.py      # NEW — SKILL_DESCRIPTIONS data table + get_description() (cap in one place)
├── constants.py         # reused: SKILL_NAME_MAX_LENGTH, SKILL_DESCRIPTION_MAX_LENGTH,
│                        #         + SKILL_BODY_MAX_TOKENS (new) ; marker name deprecated
├── errors.py            # + SkillLintError, SkillMaterializationError (+ name_frontmatter_mismatch)
├── claude/__init__.py   # class vars only — NO setup() override
└── generic/__init__.py  # class vars only + resolve_skills_dir + options — NO setup() override

src/bookwright/resources/commands/   # READ-ONLY input (iteration 8): 10 *.md + references/

src/bookwright/commands/init/scaffold.py  # imports fs primitives from io.fs (moved out);
                                          # step 4 updated: drop marker pre-record, pass the
                                          # live BackupLedger to setup() (ledger=ledger)

tests/io/
└── test_fs.py           # MOVED/EXTENDED — BackupLedger/mkdir_tracked/write_bytes_atomic +
                         #   NullLedger no-op (relocated from the init scaffold tests)

tests/integrations/
├── test_materialize.py        # NEW — generate_skill_md unit + roster + token sub + refs +
│                              #   ledger recording + name_frontmatter_mismatch
├── test_skill_lint.py         # NEW — lint_skill_md pass/fail invariants (incl. FR-013)
├── test_materialize_idempotent.py  # NEW — US2 idempotency (byte-for-byte)
└── test_setup_stub.py         # REWRITTEN → test_setup_materialize.py contract (+ orphan rollback)

tests/commands/init/           # E2E: init in tmp_path → every SKILL.md lints clean +
                               #   pre-existing skills_dir abort → zero orphans (SC-008)
```

**Structure Decision**: Single-project src-layout, decomposed **by responsibility**
(not by line surgery). `base.py` stays the plugin *contract* — `SkillsIntegration`
plus **one shared `setup()`** (the iteration-3 "implemented once here; no subclass
overrides it" stance is kept: the only per-integration variation already lives behind
`resolve_skills_dir()` and the capability flags, so two identical `setup()` bodies
would violate DRY). The new concerns get their own modules:

- `materialize.py` — `generate_skill_md()` and its private helpers (fs-mutating).
- `lint.py` — `lint_skill_md()` + `approx_tokens()` (pure, read-only; reusable by the
  iteration-11 validation system, which depends on this iteration).
- `descriptions.py` — the bulky bilingual `SKILL_DESCRIPTIONS` data table, isolated
  from logic with the 1024-char cap asserted in one place (FR-004, mirrors Spec Kit's
  description dict beside its generator, design § 11.4). In v0 the dict mirrors the
  source frontmatter under a CI equality gate (SC-009) — the dict is the authoritative
  read seam, the gate prevents silent drift, and a deliberate future divergence is a
  one-line, reviewed change.
- `io/fs.py` — the transactional-fs layer (`FileLedger` Protocol, `NullLedger`,
  `BackupLedger`, `mkdir_tracked`, `write_bytes_atomic`) lifted out of `init/scaffold.py`
  so both `commands.init` and `integrations` depend on it (a single, tested
  rollback-recording primitive instead of two divergent copies). `scaffold.py` keeps the
  command-specific orchestration (resource-tree render, manifest dump, the apply flow).

This keeps every module well under the 500-line cap (Principle IV — decompose *before*
the limit) and makes the module boundaries mirror the test-file boundaries. **Import
cycle note**: `materialize.py` imports `SkillsIntegration` under `TYPE_CHECKING` only
(it reads `integration.key` / capability flags structurally at runtime), the same
pattern `base.py` already uses for `Manifest`; `base.py` imports `generate_skill_md`
at module level — no runtime cycle. The fs extraction keeps the dependency graph acyclic:
`commands.init → io.fs` and `integrations.{base,materialize} → io.fs`, while `io` imports
neither `commands` nor `integrations`.

## Complexity Tracking

> No constitutional violations. Section intentionally empty.
