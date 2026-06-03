# Contract: End-to-End Test Suite

**Branch**: `011-release-prep` | **Phase**: 1 | Maps to FR-006…FR-009, SC-002

Three test files under `tests/e2e/` (a new subpackage; `tests/e2e/__init__.py`).
All drive the CLI **in-process** via `typer.testing.CliRunner` against
`bookwright.cli:app` (D1), so they contribute to `--cov` (FR-009). Each file
**≤ 500 lines** (Principle IV). Helper for copying a fixture into `tmp_path`
lives in `tests/e2e/conftest.py` or reuses the root `tests/conftest.py`.

---

## C1 — `tests/e2e/test_full_workflow.py` (FR-006)

**Scenario**: empty dir → validated project (spec US1 AS-1).

```
GIVEN an empty tmp_path
WHEN  invoke `init <name> --integration claude` (or --here)
THEN  exit 0; manifest.toml, bible/, outline/, manuscript/, skills dir exist
WHEN  edit manifest.toml (e.g. set book metadata) AND edit bible/constitution.md
THEN  edits persist (plain-text, Principle I)
WHEN  invoke `graph build`
THEN  exit 0; bible/graph.ttl written; report: 0 skips, 0 unknown_keys
WHEN  invoke `graph query "<SPARQL counting entities>" --json`
THEN  stdout is a single JSON doc {"status":"ok","results":[...],"count":N}
      with the expected entity counts
WHEN  invoke `validate` (and `validate --json`)
THEN  exit 0 (zero `error`-severity); JSON body well-formed on stdout only
```

**Assertions**:
- Every `--json` invocation: `json.loads(result.stdout)` succeeds and stdout
  carries **only** that document (Principle IX).
- Final state is a valid project (validate reports clean).
- At least one step asserts a non-zero exit + structured JSON error on a
  deliberately broken input (e.g. `graph query` with malformed SPARQL → exit
  3), proving the fault model end-to-end.

---

## C2 — `tests/e2e/test_skills_materialization.py` (FR-007)

**Scenario**: every generated `SKILL.md` satisfies agentskills.io (spec US2
AS-2; Principle VII).

```
GIVEN a tmp_path project freshly `init`-ed (both `claude` and `generic`)
WHEN  call `integrations.lint.lint_skill_md(<skills_dir>/<name>/)` for every
      materialized skill
THEN  it does not raise — i.e. for each skill:
        - frontmatter parses as valid YAML
        - `name` is present, `< SKILL_NAME_MAX_LENGTH`, and == its parent dir
        - `description` is present and `< SKILL_DESCRIPTION_MAX_LENGTH`
      (the test reuses the shipped linter; it does NOT re-encode the bounds)
```

**Assertions**:
- Parametrized over both integrations (`claude` → `.claude/skills/`,
  `generic` → `.agents/skills/`).
- Count of materialized skills equals the count of source commands shipped
  (the 10 authoring commands).
- No `.claude/commands/` or `.agents/commands/` directory is ever created
  (Principle VI negative assertion).

---

## C3 — `tests/e2e/test_integration_swap.py` (FR-008)

**Scenario**: claude → generic swap via re-init (spec US2 AS-3; clarified
2026-06-03).

```
GIVEN a tmp_path project `init --integration claude` (skills under .claude/skills/)
WHEN  edit manifest.toml [integration] → generic
AND   invoke `init --here --force`
THEN  exit 0
AND   skills are correctly materialized under .agents/skills/ (valid SKILL.md set)
AND   the test makes NO assertion about removal of the old .claude/skills/ dir
```

**Assertions**:
- Positive: `.agents/skills/<name>/SKILL.md` set exists and is valid.
- Explicitly **does not** assert `.claude/skills/` is gone (no cleanup
  behavior added this iteration — spec Assumptions / edge case).

---

## Cross-cutting contract rules

- **R1**: No E2E test writes outside `tmp_path`; fixtures are consumed via
  `shutil.copytree(fixture, tmp_path/...)` (D2).
- **R2**: E2E tests run in the default pytest selection (no `manual`
  marker) → they count toward the > 80% coverage gate (FR-009, SC-005).
- **R3**: Any subprocess-based smoke (real `bookwright` on PATH / installed
  wheel) lives **separately** and is the only path exempt from coverage.
