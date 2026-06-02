# Contract: `generate_skill_md` (shared materializer)

`src/bookwright/integrations/materialize.py`

```python
def generate_skill_md(
    command_path: Traversable | Path,
    target_dir: Path,
    integration: SkillsIntegration,
    *,
    ledger: FileLedger,
) -> Path | None:
    """Materialize one source command into a per-skill directory.

    Returns the written SKILL.md path, or None if the skill already existed
    (idempotency skip). Raises SkillLintError on a lint failure (after removing
    the half-written skill dir). Raises SkillMaterializationError on a dangling
    reference or a frontmatter `name` ≠ filename-stem mismatch.

    Every directory and file it creates is recorded through `ledger`
    (a FileLedger; NullLedger for standalone calls) so init can roll them back
    (FR-019).
    """
```

## Inputs

- `command_path` — packaged source `<name>.md` (`importlib.resources` Traversable or a
  filesystem `Path`). Frontmatter read via `bookwright.io.frontmatter.parse_frontmatter`.
- `target_dir` — the integration's resolved `skills_dir` **absolute** path
  (`project_root / resolve_skills_dir(...)`), already containment-checked by `setup()`.
- `integration` — the calling `SkillsIntegration` (provides `key`, capability flags;
  `supports_dynamic_context` is **read but not acted on** in v0 — FR-011).
- `ledger` — a `FileLedger` (the narrow rollback-recording protocol from `bookwright.io.fs`,
  satisfied structurally by `BackupLedger`; `NullLedger` no-ops it for standalone calls).
  The materializer creates dirs via `mkdir_tracked(.., ledger)` and writes files via
  `write_bytes_atomic(.., ledger)`, so every created path is rolled back on a failed
  `init` — including over a pre-existing `skills_dir` (FR-019).

## Behaviour (must)

1. Derive `name` from the source filename stem (the single source of truth);
   `skill_dir = target_dir / name`. **Validate** `fm.metadata.get("name") == name`; a
   mismatch → `SkillMaterializationError(rule="name_frontmatter_mismatch")` (FR-020) —
   the frontmatter `name` is checked, never silently ignored.
2. **Idempotency** (FR-014): if `skill_dir / "SKILL.md"` exists → return `None`, write
   nothing.
3. Resolve `description = descriptions.get_description(name, fm.metadata["description"])`
   (R3, FR-004; `SKILL_DESCRIPTIONS` lives in `descriptions.py`); assert
   `< SKILL_DESCRIPTION_MAX_LENGTH`.
4. Transform body: `body.replace("{ARGS}", "$ARGUMENTS")` (FR-007); assert no `{ARGS}`
   or `{SCRIPT}` token remains (SC-003); leave all other content intact (FR-018). Emit
   **no** `` !`…` `` injection (FR-011/012).
5. **Resolve cited references — pure, no filesystem mutation**: collect each distinct
   `references/<file>.md` cited in the body and resolve it to its packaged source
   `commands/references/<file>.md`. A citation with no matching source file →
   `SkillMaterializationError` (`dangling_reference`), raised **before any directory is
   created or file written**. Together with the step-1 `name_frontmatter_mismatch` check,
   this makes every *authoring* error pre-write: a rejected source leaves **zero** on-disk
   state — no half-written `skill_dir` to clean up, in `init` *or* standalone/`NullLedger`
   callers. Returns the resolved `(file, source_path)` copy-list, consumed in step 7.
6. Build frontmatter (`name`, `description`,
   `license=fm.metadata.get("license", DEFAULT_SKILL_LICENSE)`,
   `metadata.author="bookwright"`, `metadata.version=bookwright.__version__`) →
   `yaml.safe_dump(allow_unicode=True, sort_keys=False)` between `---` fences (R5,
   FR-003/005/006). The license **honours a source-declared `license`** and falls back
   to `DEFAULT_SKILL_LICENSE` (`"Apache-2.0"`, `constants.py`) — implementing FR-005 as
   written ("inherited when the source does not specify one"). No v0 source declares a
   license, so every materialized skill inherits `Apache-2.0` (A-002); the conditional
   read keeps spec and code aligned and is future-proof at zero cost.
7. **All writes happen here — the single first mutation point** (every created path
   recorded through `ledger` — FR-019): create `skill_dir` via `mkdir_tracked(.., ledger)`,
   write `SKILL.md` via `write_bytes_atomic(.., ledger)`, and copy each reference resolved
   in step 5 into `skill_dir / "references" / <file>.md` (creating `skill_dir/references/`
   via `mkdir_tracked(.., ledger)`, writing via `write_bytes_atomic(.., ledger)`, FR-010).
   Then **lint** the result via `lint_skill_md` (see sibling contract). On `SkillLintError`,
   delete `skill_dir` and re-raise (FR-016 — "no invalid SKILL.md on disk"); the now-stale
   ledger entries are inert at rollback (it guards with `if entry.target.exists()`). A lint
   failure is thus the **only** post-write error and the only one that needs on-disk
   cleanup — authoring errors never reach this point.
8. Never write outside `target_dir` (FR-017).

## `setup()` driver (single shared method in `base.py` — FR-001)

One `setup()` lives in `base.py`; **neither v0 subclass overrides it** (the
iteration-3 stance is kept — the only per-integration variation is already behind
`resolve_skills_dir()` and the capability flags). "Rewriting both setups" (the plan
input) means this shared body now materializes for real instead of writing a marker.
`setup()` gains a keyword-only `ledger: FileLedger | None` (defaulting to `NullLedger()`),
so the iteration-3 signature is **extended, not preserved** — this is the correct
replacement for the marker pre-record that `scaffold.py` did on the integration's behalf.

```python
# base.py
from bookwright.integrations.materialize import generate_skill_md, iter_command_sources
from bookwright.io.fs import FileLedger, NullLedger, mkdir_tracked

def setup(self, project_root, manifest, parsed_options=None, *, ledger=None) -> None:
    ledger = ledger or NullLedger()
    target = (project_root / self.resolve_skills_dir(parsed_options)).resolve()
    # reuse iteration-3 containment guards (resolves_to_project_root / escapes_project_root)
    mkdir_tracked(target, ledger)
    for command_path in iter_command_sources():   # packaged roster, R4
        generate_skill_md(command_path, target, self, ledger=ledger)
```

- `materialize.py` imports `SkillsIntegration` under `TYPE_CHECKING` only (R1) — no
  runtime import cycle with `base.py`. `base.py` and `materialize.py` import the fs
  primitives from `bookwright.io.fs` (which imports neither `commands` nor
  `integrations`) — acyclic.
- Empty roster → completes, creates no skill dirs (edge case "no source commands").
- A `SkillLintError`/`SkillMaterializationError` from any command **propagates**
  (aborts this integration — FR-016); no `try/except` swallow.

## Out of scope

- No `!`shell`` auto-injection (FR-011). No `.bookwright/scripts/` wrappers (FR-008).
- No per-integration body divergence beyond `skills_dir` + token substitution (US3 AC-3).
