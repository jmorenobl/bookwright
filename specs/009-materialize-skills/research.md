# Phase 0 Research: Materialize commands as Agent Skills

All Technical Context items were resolvable from the existing codebase and the three
spec clarifications; **zero NEEDS CLARIFICATION remain**. Decisions below.

## R1 — Module decomposition of the integrations layer (revised)

- **Decision**: decompose **by responsibility**, not by line surgery. `base.py` stays
  the plugin *contract* (`SkillsIntegration` + **one shared `setup()`**). The new
  concerns get dedicated modules:
  - `materialize.py` — `generate_skill_md(command_path, target_dir, integration)` plus
    the public `iter_command_sources()` (imported by `base.py` → cross-module, so no
    leading underscore) and its private helpers (`_transform_body`,
    `_render_frontmatter`, `_copy_references`). Filesystem-mutating.
  - `lint.py` — `lint_skill_md()` + `approx_tokens()`. Pure, read-only.
  - `descriptions.py` — the bilingual `SKILL_DESCRIPTIONS` data table + a
    `get_description(name, fallback)` lookup. The 1024-char cap is asserted here, in
    one place (FR-004).
- **Rationale**: (1) SRP — materialization (writes), linting (reads), the description
  data table, and the integration contract change for different reasons and already
  have separate test files (`test_materialize.py`, `test_skill_lint.py`), so module
  boundaries mirror test boundaries. (2) Principle IV: every module stays well under
  the 500-line cap (`base.py` ≈110-130, `materialize.py` ≈140-180, `lint.py` ≈110-150,
  `descriptions.py` ≈60-120), satisfying "decompose *before* the limit". (3) `lint.py`
  is pure and reusable by the **iteration-11 validation system** (which depends on this
  iteration) without dragging in the fs-write logic — a concrete downstream consumer,
  not speculative plumbing. (4) Spec Kit precedent (`src/specify_cli/__init__.py:1059-1069`)
  keeps its description dict beside the generator (design § 11.4); a dedicated data
  module is the cleanest expression of that.
- **`setup()` is shared, not per-subclass**: the iteration-3 stance ("`setup()`
  implemented once here; no v0 subclass overrides it") is **kept**. The only
  per-integration variation (`skills_dir`, capability flags) is already abstracted
  behind `resolve_skills_dir()` and the `supports_*` flags, so the iteration-9
  `setup()` body (resolve target → containment guards → loop over `generate_skill_md`)
  is identical for both integrations. Two override copies would violate DRY. The
  `/speckit-plan` input "reescribe los setup()" is read as "make their behaviour
  materialize for real", not "add two twin override methods".
- **Import-cycle resolution**: `generate_skill_md` takes `integration:
  SkillsIntegration` for typing but at runtime only reads `integration.key` and the
  capability flags (structural). So `materialize.py` imports `SkillsIntegration` under
  `if TYPE_CHECKING:` only — the exact pattern `base.py` already uses for `Manifest` —
  while `base.py` imports `generate_skill_md` at module level. No runtime cycle; no
  ad-hoc `Protocol` needed.
- **Alternatives rejected**: (a) putting `generate_skill_md` + `SKILL_DESCRIPTIONS`
  inside `base.py` (the original plan input) — pushes `base.py` toward 350-450 lines and
  mixes three concerns in the contract module; (b) per-subclass `setup()` overrides —
  DRY violation, reopens an iteration-3 decision; (c) folding `lint.py` into
  `materialize.py` — couples the pure validator to fs-write code and blocks clean reuse
  by iteration 11; (d) a `Protocol` in `materialize.py` to dodge the import — needless
  indirection when `TYPE_CHECKING` already solves it.

## R2 — `{ARGS}` token substitution mechanism

- **Decision**: `string.Template`. Rewrite source bodies' `{ARGS}` → render to
  `$ARGUMENTS`. Because the **only** token is `{ARGS}`, the substitution is a single
  literal replacement; `string.Template` (or an equally simple `str.replace("{ARGS}",
  "$ARGUMENTS")`) is sufficient and avoids a regex-injection surface.
- **Rationale**: user offered `string.Template` *or* `re`; the source contract has
  exactly one token (`{ARGS}`, FR-007) and **no** `{SCRIPT}` (FR-008), so a literal
  map is the least-surprise choice. `string.Template.safe_substitute({"ARGS":
  "$ARGUMENTS"})` after rewriting `{ARGS}`→`${ARGS}` works, but a direct
  `body.replace("{ARGS}", "$ARGUMENTS")` is clearest. **Chosen: literal `str.replace`,
  with a post-condition assert that no `{ARGS}`/`{SCRIPT}` token survives** (SC-003).
- **Alternatives rejected**: full Jinja2 render — overkill and dangerous (source prose
  contains `{ }` and backticks that Jinja would misparse); the bodies are *copied*, not
  *templated*.

## R3 — `description` source and the 1024-char cap

- **Decision**: `SKILL_DESCRIPTIONS[command_name]` is **authoritative** (clarification
  Q1, FR-004). The dict is seeded from the iteration-8 canonical bilingual frontmatter
  `description` text already shipped in each source `*.md`. When a command has **no**
  dict entry, fall back to the source frontmatter `description`. The materializer
  asserts `len(description) < 1024` (FR-004, edge case "description over the cap") and
  the linter re-checks it; over-cap is a hard lint failure (no truncation — Principle
  VII forbids silent fixing).
- **Rationale**: single source of truth for triggers; one place to cap. Seeding from
  the iteration-8 text means the bilingual ES/EN triggers (`[[user-bilingual]]`) carry
  through unchanged.
- **Alternatives rejected**: deriving description from the body's first paragraph
  (loses curated triggers); per-integration description divergence (no v0 need).

## R4 — Reading the source roster (packaged resources)

- **Decision**: enumerate via `importlib.resources.files("bookwright.resources")
  .joinpath("commands")`, iterate `*.md` at the top level (excluding the `references/`
  subdir). Verified working even though `commands/` has no `__init__.py` — the whole
  `resources` tree is force-included in the wheel
  (`pyproject.toml [tool.hatch.build.targets.wheel.force-include]`).
- **Rationale**: mirrors the existing `render_resource_tree` /
  `copy_resource_file` pattern in `commands/init/scaffold.py` (uses `files()` +
  `as_file()`); no new packaging config needed; survives both editable and wheel
  installs (Principle III intent).
- **Alternatives rejected**: hard-coding the ten command names — duplicates the
  roster (already pinned by iteration-8 tests) and rots when a command is added;
  instead derive from disk and (optionally) cross-check against the known roster in
  tests.

## R5 — Writing valid YAML frontmatter for the generated `SKILL.md`

- **Decision**: build the frontmatter as an ordered dict (`name`, `description`,
  `license`, `metadata: {author, version}`) and serialize with
  `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)`, wrapped in `---` fences,
  then concatenate the substituted body. Round-trip guaranteed because the linter and
  iteration-8 `parse_frontmatter` both read it back with `yaml.safe_load`.
- **Rationale**: hand-formatting multi-line bilingual descriptions risks invalid YAML
  (the very thing the linter rejects); `safe_dump` with `allow_unicode` keeps ES
  accents readable and is already a declared dependency (`pyyaml`, Constitution 1.2.0).
  `sort_keys=False` preserves the spec's field order (FR-003/005/006).
- **Alternatives rejected**: a Jinja2 frontmatter template (fragile for arbitrary
  description text); reusing iteration-8's `>-` block scalar style by hand (no writer
  exists; `safe_dump` chooses a valid style automatically).

## R6 — Token-budget estimation for the Tier-2 body cap

- **Decision**: reuse the iteration-8 `approx_tokens` heuristic — `tiktoken` count if
  importable, else `ceil(len(text)/4)` — exposed as a helper in `integrations/lint.py`.
  Cap constant `SKILL_BODY_MAX_TOKENS = 5000` added to `constants.py`. Bodies are copied
  unchanged from already-budget-passing iteration-8 sources, so this is a regression
  guard, not a new constraint.
- **Rationale**: identical heuristic to the source-side gate keeps the two checks
  consistent (a source that passed iteration 8 must pass here); no hard `tiktoken`
  dependency added (it is not in the runtime set — optional import only).
- **Alternatives rejected**: a byte-length cap (diverges from the source gate);
  mandating `tiktoken` (would require a constitutional amendment).

## R7 — Idempotency granularity and rollback integration

- **Decision**: idempotency is checked per-`SKILL.md` (clarification A-005): if
  `<skills_dir>/<command>/SKILL.md` exists, skip the whole skill (no overwrite, no
  re-copy of its `references/`). A missing skill is (re)generated in full. The
  materializer writes through the init `BackupLedger` so `init` rollback can unwind a
  failed run; the marker-specific pre-record in `scaffold.py` step 4 (the
  `.bookwright-skills-placeholder` handling) is removed since no marker is written now.
- **Rationale**: protects hand-edits (US2, SC-005, FR-014) with the simplest possible
  rule; reuses the existing ledger (`record_new_file`/`write_bytes_atomic`/
  `mkdir_tracked`) rather than inventing a second rollback path.
- **Open coupling note**: `setup()`'s signature `(project_root, manifest,
  parsed_options)` does not carry the ledger. Two options surface in Phase 1: (a)
  `setup()` returns the list of created paths and `scaffold.py` records them; (b) the
  materializer writes atomically and `init`'s existing top-level rollback removes the
  `skills_dir` subtree it created. **Chosen (data-model § 5): (b)** — `setup()` keeps
  its iteration-3 signature; on lint failure the materializer cleans up *its own*
  partially-written skill dir (FR-016 "no invalid SKILL.md on disk"), and whole-`init`
  failure is handled by the existing ledger that already tracks the `mkdir`'d
  `skills_dir`. This avoids widening the `setup()` contract mid-iteration.

## R8 — Lint failure = hard abort (FR-016) and the dynamic-context invariant (FR-013)

- **Decision**: `lint_skill_md(skill_dir)` raises `SkillLintError` (structured,
  `to_dict()`-capable like the existing integration errors) on the first violation;
  `setup()` does **not** catch it — it removes the half-written offending skill dir and
  propagates, aborting that integration's materialization (FR-016, clarification A-006).
  The linter also enforces FR-013: any `` !`…` `` dynamic-context injection present in a
  body must either read a project file or invoke `bookwright`, never point at a
  non-existent wrapper / absent executable. In v0 the materializer emits **no**
  injection (FR-011), so this guards user customizations and a crafted invalid sample
  (SC-006).
- **Rationale**: matches Principle VII ("fail loudly … silent truncation or auto-fixing
  is forbidden") and the three clarifications. Reusing the `_IntegrationError`
  `to_dict()` shape means iteration-10's error-envelope consolidation can wrap it
  without a new format.
- **Alternatives rejected**: skip-and-warn (explicitly rejected in clarification Q3);
  best-effort truncation of an over-cap description (Principle VII violation).
