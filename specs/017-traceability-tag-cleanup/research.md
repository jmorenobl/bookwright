# Research: Traceability Tag Cleanup

Phase 0 output. Resolves every NEEDS-CLARIFICATION and records the decisions
that make `/speckit-implement` mechanical.

## Sweep result (ground truth, 2026-06-05)

```
grep -rnIE '\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+' src/ tests/
```

- **73 occurrences on 67 lines across 48 files** (46 `.py` + 2 `.toml`).
- Every hit is in a `#` comment or a `"""docstring"""`. **Zero** hits in a
  test name, assertion, or string literal → FR-008 and FR-001/002 do not
  conflict (confirms the spec's pre-check assumption).
- Only **2** hits live under `src/`; the other 65 lines are under `tests/`.

## D1 — Conversion taxonomy: four mechanical edit classes

**Decision**: classify each line into exactly one of four actions. No hit
needs a fifth.

| Class | When | Action | Spec basis |
|---|---|---|---|
| **strip-token** | the line *already* carries a durable `FR`/`SC`/`D`/`§` ref next to the forbidden tag | delete only the forbidden token + its now-orphaned punctuation; freeze every surrounding ref byte-for-byte | FR-003, FR-007 |
| **relabel** | a decorative section marker (`# --- US2: … ---`) or docstring header (`"""US1 — …"""`) keyed by a forbidden ID | rewrite to a behaviour/content label with the ID gone | FR-005 |
| **remove** | a bare bookkeeping parenthetical (`(T021)`, `(US1, T013)`) whose surrounding prose is already self-describing | delete the parenthetical; keep the prose | FR-004 (carried no rationale) |
| **neutral-prose** | the tag carried a *why* but has no durable equivalent | rewrite to prose explaining the why, no ID | FR-004 (carried rationale) |

**Rationale**: the headline finding is that **strip-token covers every
genuinely-traceable hit**, because in this codebase the durable ref was
already written alongside the story/task tag (e.g. `(US2, FR-011..FR-016)`,
`SC-009 (T020)`). So FR-003 ("replace with the equivalent durable reference")
is satisfied by *deletion of the forbidden token alone* — the equivalent ref
is already present. No owning-spec lookup is required to invent a new number,
which eliminates the main risk (mis-resolving against the wrong iteration's
restarted numbering) and the main scope creep.

**Alternatives considered**: (a) bulk-delete every parenthetical — rejected,
destroys the durable refs and the navigational value (US2). (b) Resolve every
US header to its owning-spec FR — rejected as unnecessary work: the headers
are *file-level* docstrings naming what the test file covers; a
behaviour-descriptive relabel is more durable than a story number that
restarts per iteration.

## D2 — Owning-iteration resolution

**Decision**: a file's durable refs resolve against the iteration whose
`src/`/`tests/` subtree contains it (CONTRIBUTING.md rule 1). In practice this
is only consulted to *sanity-check* that an already-present `FR`/`SC`/`D` ref
belongs to the file's owner — we never import another iteration's numbers
(FR-006). The two `src/` edits: `core/_research_block.py` → iteration 013;
`integrations/base.py` → iteration 009. No ambiguity arose: no hit needed a
borrowed number, so the "ambiguous owner" edge case degrades to *remove* or
*neutral-prose*, never a wrong citation.

## D3 — No-regression gate mechanism

**Decision** (locked by spec Clarifications): a single `pytest` test,
`tests/meta/test_no_traceability_tags.py`. **No** pre-commit hook, **no** ruff
custom rule.

**Rationale**: it rides `uv run pytest` and thus CI on every push/PR
(Principle VIII) — the minimal deliverable that fully satisfies FR-010 /
SC-004. Pre-commit wiring is a trivial, deliberately out-of-scope future add.

**Gate self-match — verified, not assumed**: the forbidden patterns stored as
a raw regex string do **not** match their own source, because the `[0-9]`
character classes interrupt the literal digit run the patterns require:

```
re.findall(PATTERN, r"\bT0[0-9]{2}\b|\bUS-?[0-9]+\b|\+US[0-9]+")  →  []
re.findall(PATTERN, "T0xx US-x +USx")                              →  []   # placeholders safe
re.findall(PATTERN, "FR-021 SC-009 D-2 § 20.5 iteration 9")        →  []   # no false positives
re.findall(PATTERN, "T013 US2 +US3")                               →  ['T013','US2','+US3']
```

So: docs may use `T0xx`/`US-x`/`+USx` placeholders freely; permitted
`FR`/`SC`/`D`/`§`/"iteration N" tokens never trip the gate (FR-011); and the
gate's own pattern literal is inert. The gate still excludes its own
`__file__` as belt-and-suspenders and so a future maintainer who pastes a
*real* example tag into the gate's docstring doesn't self-trip it.

## D4 — Scan surface

**Decision**: the gate walks text files under `src/` and `tests/` only,
skipping `__pycache__` and binaries (decode-as-utf-8, skip on
`UnicodeDecodeError`). `specs/`, `docs/`, design docs, and the repo root are
out of scope (FR-012 — their task/story IDs are legitimate). `.toml` and other
text extensions are included (two `.toml` fixtures carry tags today).

## Full per-line classification (drives /speckit-tasks)

Action key: **S** = strip-token, **L** = relabel, **R** = remove, **P** =
neutral-prose. "Keep" lists durable refs that MUST survive byte-for-byte.

**Row reconciliation**: 2 (src) + 2 (tests root/fixtures) + 15 + 11 + 4 + 3 + 9
+ 5 + 1 + 15 (the eight tests subdirs) = **67 lines**, matching the sweep above.

### src/ (2)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `core/_research_block.py:1` | `US2` | S | keep `FR-011..FR-016`; drop `US2, ` |
| `integrations/base.py:11` | `T013` | R | drop `(T013)`; prose "implemented once here; no v0 subclass overrides it" already carries the why |

### tests/ (top-level harness + fixtures) (2)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `conftest.py:3` | `T004` | S | keep `D1/D2`; drop `T004, ` |
| `fixtures/test_fixtures.py:1` | `US1` | S | keep `SC-001`; drop `US1, ` |

### tests/commands (15)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `conftest.py:60` | `T047` | R | keep "round-4 audit"; drop `, T047` |
| `graph/test_research_build.py:4` | `US1-US3` | L | "proving sources, findings and anchors end to end (quickstart 1-3)…" |
| `graph/test_research_build.py:67` | `US1` | L | `# --- sources become typed nodes with full provenance ---` |
| `graph/test_research_build.py:100` | `US2` | L | `# --- findings reify on E13 and link to the narrative ---` |
| `graph/test_research_build.py:148` | `US3` | L | `# --- anchors constrain the fiction + the payoff query ---` |
| `init/test_init_research_scaffold.py:1` | `US3` | S | keep `FR-008/009/014a`; drop `US3, ` |
| `init/test_init_research_scaffold.py:34` | `US3-1` | L | `# the directory ships two real files; the legacy single file is gone.` |
| `init/test_init_research_scaffold.py:62` | `T014` | R | keep `FR-014a`; drop `(depends on T014) ` |
| `init/test_init_research_scaffold.py:70` | `US3-2` | S | keep `FR-008`; drop `/ US3-2` |
| `test_init_default.py:1` | `US1` | L | `"""bookwright init <NAME> — default path."""` |
| `test_init_deprecated_flags.py:1` | `US5` | L | `"""--ai, --ai-skills, --ai-commands-dir."""` |
| `test_init_helpers.py:265` | `T021` | R | keep "iteration 9"; drop `, T021` |
| `test_init_here.py:1` | `US2` | L | `"""bookwright init --here."""` |
| `test_init_integrations.py:1` | `US3` | L | `"""--integration and --integration-options."""` |
| `test_init_no_git.py:1` | `US4` | L | `"""--no-git and git-missing warning."""` |

### tests/core (11)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `fixtures/valid_full.toml:1` | `US1`,`T012` | R | keep "Fully-populated valid manifest fixture"; drop `(US1, T012)` |
| `fixtures/valid_minimal.toml:1` | `US1`,`T013` | R | keep "Minimal valid manifest fixture"; drop `(US1, T013)` |
| `test_build.py:1` | `US4` | L | `"""Build/derive — FR-015, FR-016, FR-017, SC-004."""` (keep refs) |
| `test_future_version.py:1` | `US5` | L | `"""Future manifest_version handling — FR-013, FR-014, SC-006."""` |
| `test_future_version.py:43` | `US2` | R | drop `(US2 path)`; keep "AS3 / regression guard …" |
| `test_future_version.py:54` | `US2` | R | drop `(US2 path)` |
| `test_load_invalid.py:1` | `US2` | L | keep `FR-002, FR-004 through FR-011, FR-013`; drop `US2 - Acceptance Scenarios 1-9` header |
| `test_load_valid.py:1` | `US1` | L | keep `FR-001, FR-003, FR-022` |
| `test_research_block.py:1` | `US2` | S | keep `RB-1..RB-8`; drop `US2, ` |
| `test_version_gate.py:1` | `US3` | L | keep `FR-012, SC-003` |
| `test_write.py:1` | `US4` | L | keep `FR-018..FR-021, SC-005` |

### tests/e2e (4)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `conftest.py:4` | `T004` | R | drop `(T004)`; keep "tests/conftest.py … re-exports" |
| `test_research_workflow.py:127` | `US2` | S | keep `FR-008..FR-011`; drop `US2 / ` |
| `test_research_workflow.py:191` | `US2` | S | keep `FR-012`; drop `US2 / ` |
| `test_research_workflow.py:230` | `US3` | S | keep `FR-013, FR-014`; drop `US3 / ` |

### tests/golem (3)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `test_provenance_entities.py:70` | `US1` | L | `# --- Source ---` |
| `test_provenance_entities.py:122` | `US2` | L | `# --- Finding ---` |
| `test_provenance_entities.py:170` | `US3` | L | `# --- Anchor ---` |

### tests/integrations (9)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `conftest.py:48` | `US5` | P | "Lets the plugin-contract tests safely mutate the registry…" |
| `test_materialize_idempotent.py:1` | `US2` | L | keep `FR-014, SC-005, A-005` |
| `test_metadata.py:1` | `US4` | L | keep `FR-006..FR-011` |
| `test_option_parser.py:1` | `US3` | L | keep `FR-016..FR-021, SC-005` |
| `test_plugin_contract.py:1` | `US5` | L | keep `FR-031, SC-007, research R8` |
| `test_plugin_contract.py:41` | `T010` | R | keep "iteration 9"; drop `(T010)` |
| `test_registry.py:1` | `US1` | L | keep `FR-001..FR-005` |
| `test_research_skill.py:1` | `US1` | S | keep `SC-001`; drop `US1, ` |
| `test_skill_capabilities.py:1` | `US3` | L | keep `FR-013, SC-006` |

### tests/io (5)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `test_fs.py:4` | `T021` | R | keep "iteration 9"; drop `, T021` |
| `test_research.py:86` | `US1` | L | `# --- sources.md ---` |
| `test_research.py:146` | `US2` | L | `# --- findings ---` |
| `test_research.py:209` | `US3` | L | `# --- anchors ---` |
| `test_research_format.py:1` | `US1` | S | keep `SC-004/005`; drop `US1, ` |

### tests/resources (1)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `test_command_body.py:7` | `US1`,`US2` | R | keep "covers all 12 files uniformly"; drop `(US1 + US2) ` |

### tests/validation (15)

| File:line | Forbidden | Action | Keep / result |
|---|---|---|---|
| `conftest.py:1` | `T019` | R | drop `(T019)`; keep "Shared fixtures + scaffolding for the validation suite" |
| `test_base.py:1` | `T008` | R | drop `(T008)`; keep "Core finding types + the cached context accessors" |
| `test_character_presence.py:1` | `T021` | R | drop `(T021)`; keep behaviour prose |
| `test_command.py:1` | `US1`,`T028` | L | `"""bookwright validate integration — baseline.` |
| `test_command.py:149` | `T032` | L | `# --- --json, --scope, --severity, CI gate ---` (also drop "User Story 2:") |
| `test_command.py:268` | `T036` | L | `# --- [validators] config + custom validators ---` (also drop "User Story 3:") |
| `test_factual_anchor.py:1` | `US1`,`T006` | L | `"""factual_anchor validator — structural audit + the drift-guard.` |
| `test_factual_anchor.py:276` | `US2` | L | `# --- R5 anachronism ---` (keep R5) |
| `test_factual_anchor.py:349` | `US3` | L | `# --- discovery / selection / inert / scope ---` |
| `test_focalization.py:1` | `T023` | R | drop `(T023)` |
| `test_queries.py:1` | `T012` | R | drop `(T012)` |
| `test_registry.py:1` | `T035` | S | keep `FR-004..007, D2/D7`; drop `T035, ` |
| `test_report.py:1` | `T031` | S | keep `D13.3`; drop `T031, ` |
| `test_setting_continuity.py:1` | `T022` | R | drop `(T022)` |
| `test_temporal.py:1` | `T020` | S | keep `FR-015 … SC-009`; drop ` (T020)` |

**Note on "User Story N" prose**: `test_command.py:149/268` also contain the
words "User Story 2/3", which do *not* match the gate regex (no `US<digit>`
token). They are dropped during the same relabel for cleanliness, but their
removal is not required to pass the gate.

**Note on result strings**: the "result" column is the intended replacement,
not a byte-exact diff. `/speckit-implement` produces the exact edit per file
and confirms via `git diff` that only comments/docstrings changed (FR-008).
