# Contract: `generate_skill_md` (shared materializer)

`src/bookwright/integrations/materialize.py`

```python
def generate_skill_md(
    command_path: Traversable | Path,
    target_dir: Path,
    integration: SkillsIntegration,
) -> Path | None:
    """Materialize one source command into a per-skill directory.

    Returns the written SKILL.md path, or None if the skill already existed
    (idempotency skip). Raises SkillLintError on a lint failure (after removing
    the half-written skill dir). Raises SkillMaterializationError on a dangling
    reference.
    """
```

## Inputs

- `command_path` — packaged source `<name>.md` (`importlib.resources` Traversable or a
  filesystem `Path`). Frontmatter read via `bookwright.io.frontmatter.parse_frontmatter`.
- `target_dir` — the integration's resolved `skills_dir` **absolute** path
  (`project_root / resolve_skills_dir(...)`), already containment-checked by `setup()`.
- `integration` — the calling `SkillsIntegration` (provides `key`, capability flags;
  `supports_dynamic_context` is **read but not acted on** in v0 — FR-011).

## Behaviour (must)

1. Derive `name` from the source filename stem; `skill_dir = target_dir / name`.
2. **Idempotency** (FR-014): if `skill_dir / "SKILL.md"` exists → return `None`, write
   nothing.
3. Resolve `description = descriptions.get_description(name, fm.metadata["description"])`
   (R3, FR-004; `SKILL_DESCRIPTIONS` lives in `descriptions.py`); assert
   `< SKILL_DESCRIPTION_MAX_LENGTH`.
4. Transform body: `body.replace("{ARGS}", "$ARGUMENTS")` (FR-007); assert no `{ARGS}`
   or `{SCRIPT}` token remains (SC-003); leave all other content intact (FR-018). Emit
   **no** `` !`…` `` injection (FR-011/012).
5. Build frontmatter (`name`, `description`,
   `license=fm.metadata.get("license", DEFAULT_SKILL_LICENSE)`,
   `metadata.author="bookwright"`, `metadata.version=bookwright.__version__`) →
   `yaml.safe_dump(allow_unicode=True, sort_keys=False)` between `---` fences (R5,
   FR-003/005/006). The license **honours a source-declared `license`** and falls back
   to `DEFAULT_SKILL_LICENSE` (`"Apache-2.0"`, `constants.py`) — implementing FR-005 as
   written ("inherited when the source does not specify one"). No v0 source declares a
   license, so every materialized skill inherits `Apache-2.0` (A-002); the conditional
   read keeps spec and code aligned and is future-proof at zero cost.
6. Copy cited references: for each distinct `references/<file>.md` matched in the body,
   copy `commands/references/<file>.md` → `skill_dir / "references" / <file>.md`
   (FR-010). A citation with no matching source file → `SkillMaterializationError`
   (`dangling_reference`).
7. Write atomically into `skill_dir`; then **lint** the result via `lint_skill_md`
   (see sibling contract). On `SkillLintError`, delete `skill_dir` and re-raise
   (FR-016 — "no invalid SKILL.md on disk").
8. Never write outside `target_dir` (FR-017).

## `setup()` driver (single shared method in `base.py` — FR-001)

One `setup()` lives in `base.py`; **neither v0 subclass overrides it** (the
iteration-3 stance is kept — the only per-integration variation is already behind
`resolve_skills_dir()` and the capability flags). "Rewriting both setups" (the plan
input) means this shared body now materializes for real instead of writing a marker.

```python
# base.py
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources

def setup(self, project_root, manifest, parsed_options=None) -> None:
    target = (project_root / self.resolve_skills_dir(parsed_options)).resolve()
    # reuse iteration-3 containment guards (resolves_to_project_root / escapes_project_root)
    target.mkdir(parents=True, exist_ok=True)
    for command_path in iter_command_sources():   # packaged roster, R4
        generate_skill_md(command_path, target, self)
```

- `materialize.py` imports `SkillsIntegration` under `TYPE_CHECKING` only (R1) — no
  runtime import cycle with `base.py`.
- Empty roster → completes, creates no skill dirs (edge case "no source commands").
- A `SkillLintError`/`SkillMaterializationError` from any command **propagates**
  (aborts this integration — FR-016); no `try/except` swallow.

## Out of scope

- No `!`shell`` auto-injection (FR-011). No `.bookwright/scripts/` wrappers (FR-008).
- No per-integration body divergence beyond `skills_dir` + token substitution (US3 AC-3).
