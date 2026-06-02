# Phase 1 Data Model: Materialize commands as Agent Skills

This iteration adds no Pydantic domain entities; it transforms files. The "entities"
below are the in-memory shapes and the on-disk artifacts the materializer reads and
writes.

## 1. Source command (read-only input)

Packaged Markdown under `bookwright.resources.commands/<name>.md` (iteration 8).

| Field | Source | Notes |
|---|---|---|
| `name` | frontmatter `name` | equals file basename; `< 64` chars (already gated upstream) |
| `description` | frontmatter `description` | bilingual ES/EN triggers; **fallback** only (R3) |
| `body` | text after frontmatter fence | contains `{ARGS}`, inline `bookwright … --json`, `references/<file>.md` citations |

Roster (10, pinned by iteration-8 tests): `bookwright-constitution`,
`bookwright-bible`, `bookwright-outline`, `bookwright-scenes`, `bookwright-draft`,
`bookwright-synopsis`, `bookwright-clarify`, `bookwright-analyze`,
`bookwright-continuity`, `bookwright-checklist`. Reference roster (6, under
`commands/references/`): `golem-character`, `golem-relationships`,
`golem-events-timeline`, `propp-functions`, `greimas-actants`, `pending-protocol`.

## 2. `SKILL_DESCRIPTIONS` (authoritative description map)

`descriptions.py` module-level data table (isolated from logic; R1).

```python
# descriptions.py
SKILL_DESCRIPTIONS: dict[str, str] = {
    "bookwright-constitution": "…bilingual trigger-bearing text…",
    # … one entry per command, seeded from the iteration-8 frontmatter text …
}

def get_description(name: str, fallback: str) -> str:
    """Authoritative lookup with source-frontmatter fallback (R3); asserts the cap."""
```

- **Invariant**: every value `< SKILL_DESCRIPTION_MAX_LENGTH` (1024). Capped in **one**
  place (`get_description` + a unit test over the table). FR-004, SC-002.
- **Lookup rule**: `get_description(name, source_frontmatter["description"])` →
  `SKILL_DESCRIPTIONS.get(name, fallback)`. Missing-key fallback to the source
  frontmatter description (R3).

## 3. Materialized `SKILL.md` frontmatter (output)

Serialized via `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)` between
`---` fences, in this field order:

| Field | Value | Requirement |
|---|---|---|
| `name` | command name (== parent dir) | FR-003, lint name==dir |
| `description` | `SKILL_DESCRIPTIONS` lookup (R3) | FR-004, `< 1024` |
| `license` | `fm.metadata.get("license", DEFAULT_SKILL_LICENSE)` → `"Apache-2.0"` in v0 (no source declares one) | FR-005, A-002 |
| `metadata.author` | `"bookwright"` | FR-006 |
| `metadata.version` | `bookwright.__version__` (e.g. `"0.0.1"`) | FR-006, A-003 |

## 4. Materialized skill directory (output)

```text
<skills_dir>/<command>/
├── SKILL.md                 # Tier 1 frontmatter + Tier 2 body
└── references/              # Tier 3, only files cited by THIS body
    └── <cited-file>.md
```

- **Body transform**: source body with every `{ARGS}` → `$ARGUMENTS` (FR-007); no
  `{ARGS}`/`{SCRIPT}` token survives (SC-003); inline `bookwright … --json` preserved
  verbatim (FR-008/009); all other instructional content unchanged (FR-018).
- **References**: each `references/<file>.md` citation found in the body is copied from
  the packaged `commands/references/<file>.md` into this skill's `references/`
  (FR-010, SC-004). A cited file missing from the source tree is a reported error
  (edge case "missing referenced file").

## 5. Idempotency & containment state (behavioural)

| Rule | Behaviour | Req |
|---|---|---|
| Existing `SKILL.md` | skip entire skill (no overwrite, no re-copy) — byte-identical | FR-014, SC-005 |
| Missing skill dir | (re)generate in full incl. its `references/` | A-005, SC-005 |
| Containment | never write outside resolved `skills_dir` (⊆ project root, iteration-3 guard reused) | FR-017, SC-007 |
| Lint failure | remove the half-written offending skill dir, raise `SkillLintError`, abort this integration | FR-016, A-006 |

**Rollback (R7 decision (b))**: `setup()` keeps its iteration-3 signature
`(project_root, manifest, parsed_options)`. On a per-skill lint failure the materializer
deletes *that* skill's directory before raising, so no invalid `SKILL.md` is left. The
existing init `BackupLedger` already tracks the `mkdir`'d `skills_dir`, so whole-`init`
rollback unwinds the rest; `scaffold.py` step 4 drops the now-obsolete
`.bookwright-skills-placeholder` pre-record.

## 6. Error envelope: `SkillLintError`

New structured error in `integrations/errors.py`, inheriting `_IntegrationError` so it
reuses the pinned `to_dict()` shape (`code`, `message`, + public attrs).

```python
class SkillLintError(_IntegrationError):
    code = "skill_lint_failed"
    def __init__(self, *, skill: str, rule: str, detail: str) -> None: ...
```

`rule` ∈ {`name_mismatch`, `description_too_long`, `body_over_budget`,
`invalid_frontmatter`, `forbidden_injection`, `dangling_reference`}. Consumed later by
iteration-10's error-envelope consolidation without format change.
