# Contract: `lint_skill_md` (ad-hoc agentskills.io linter)

`src/bookwright/integrations/lint.py`

```python
def lint_skill_md(skill_dir: Path) -> None:
    """Validate one materialized skill dir against the agentskills.io spec.

    Raises SkillLintError (rule + detail) on the FIRST violation. Returns None
    when the skill is compliant. Pure read-only; never mutates the filesystem.
    """
```

## Invariants enforced (FR-015, Principle VII)

| # | Rule (`SkillLintError.rule`) | Check | Req |
|---|---|---|---|
| 1 | `invalid_frontmatter` | `SKILL.md` exists and `parse_frontmatter` yields a non-empty `metadata` dict (valid YAML fence) | FR-015 |
| 2 | `name_mismatch` | `metadata["name"] == skill_dir.name` and `len(name) < SKILL_NAME_MAX_LENGTH` (64) | FR-003, FR-015 |
| 3 | `description_too_long` | `0 < len(metadata["description"]) < SKILL_DESCRIPTION_MAX_LENGTH` (1024) | FR-004, FR-015 |
| 4 | `body_over_budget` | `approx_tokens(body) < SKILL_BODY_MAX_TOKENS` (5000) | FR-015, edge "body over budget" |
| 5 | `forbidden_injection` | every `` !`…` `` injection in the body **invokes `bookwright`** or **reads a project file** with an allowlisted read command on a project-relative path — never an arbitrary executable, absent wrapper, or absolute/home path | FR-013, SC-006 |

- Rule 5 is the FR-013 invariant. In v0 the materializer emits no injection, so for
  generated skills rule 5 is trivially satisfied; it exists to reject **user-added** or
  future-iteration injections that target a non-existent wrapper, and is verified
  against a **crafted invalid sample** (SC-006).

### Rule 5 decision procedure (deny-by-default allowlist)

Rule 5 is specified as an explicit allowlist, **not** a denylist heuristic — guessing
"this looks like a missing wrapper" is undecidable statically and brittle; instead we
enumerate the only two valid shapes and reject everything else. For each `` !`<cmd>` ``
found in the body:

1. `argv = shlex.split(cmd)`; an empty `argv` → `forbidden_injection`.
2. **Allow** if `argv[0] == "bookwright"` (the CLI is the stable SKILL.md ↔ CLI contract).
3. **Allow** if `argv[0] in INJECTION_READ_COMMANDS` (`{"cat", "head", "tail"}`,
   `constants.py`) **and** no argument is an absolute path (`startswith("/")`) or a
   home-relative path (`startswith("~")`).
4. **Otherwise** raise `SkillLintError(rule="forbidden_injection")`.

`INJECTION_READ_COMMANDS` is file-read only — `ls`/`find` (which *list*, not *read a
file*) are deliberately excluded to stay faithful to FR-013 ("reads a project file").
The check is pure/read-only (it never stats the filesystem): the invariant is about the
*shape* of the injection, not whether the target currently exists. Out of scope for v0:
`..`-escape normalisation — the real attack surface is an arbitrary executable or an
absolute path, both rejected above; relative-path containment refinement is deferred
until an iteration actually emits injections.
- No `{ARGS}`/`{SCRIPT}` residue is asserted by the materializer (SC-003); the linter
  MAY also flag a stray `{ARGS}` as `invalid_frontmatter`-adjacent, but the primary
  guard is the materializer post-condition.

## `SkillLintError` shape

Reuses `_IntegrationError.to_dict()` (errors.py): `{code: "skill_lint_failed",
message, skill, rule, detail}`. The caller (`generate_skill_md`) deletes the offending
skill dir before the error escapes (FR-016).

## `approx_tokens` helper (lint.py)

```python
def approx_tokens(text: str) -> int:
    # tiktoken cl100k_base count if importable, else math.ceil(len(text) / 4)
```

Same heuristic as the iteration-8 source-side budget gate, so a body that passed
iteration 8 passes here (regression-guard parity, R6). `tiktoken` is an **optional**
import — not added to the runtime dependency set.

## Pass criteria (tests)

- A correctly materialized skill from every one of the 10 sources lints clean
  (SC-002 = 100%).
- A crafted skill with: name≠dir, 1024+ char description, a `!`/usr/local/bin/wrapper`
  injection, a 5000+ token body, and a malformed YAML fence each raises the matching
  `rule` (FR-013/015/016, SC-006).
