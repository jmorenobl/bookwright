# Contract: Automated validation gate (FR-030)

The pytest suite under `tests/resources/` that gates the 10 sources + references roster.
All assertions parametrize over the live files (no hard-coded copies). Frontmatter is read
with the shipped `bookwright.io.frontmatter.parse_frontmatter`.

## helpers.py additions

```python
COMMANDS_DIR = _PKG_ROOT / "resources" / "commands"
REFERENCES_DIR = COMMANDS_DIR / "references"

EXPECTED_COMMANDS: tuple[str, ...] = (
    "bookwright-constitution", "bookwright-bible", "bookwright-outline",
    "bookwright-scenes", "bookwright-draft", "bookwright-synopsis",
    "bookwright-clarify", "bookwright-analyze", "bookwright-continuity",
    "bookwright-checklist",
)

def command_files() -> list[Path]: ...      # the 10 *.md (excludes references/)
def reference_files() -> list[Path]: ...     # references/*.md
def approx_tokens(text: str) -> int: ...     # tiktoken if importable, else ceil(len/4)
```

## Test modules

### `test_command_frontmatter.py` — FR-001/002/003/004/005/006
- Exactly the 10 `EXPECTED_COMMANDS` exist at `commands/<name>.md`; no extras, no missing.
- Each parses; `name` present and `== basename`; `name` < 64 chars.
- `description` present, non-empty, `< 1024` chars.
- No `scripts` key; no `handoffs` key.

### `test_command_body.py` — FR-007..FR-014, body language
- Body non-empty.
- All eight required sections detectable (heading-keyword match, ES).
- Report-only commands (clarify, analyze, continuity, checklist) contain an explicit
  "no escribe / report-only" statement; generative commands name concrete write targets.
- Body looks Spanish (`helpers.looks_spanish`).
- Generative commands (`helpers.GENERATIVE_COMMANDS` — constitution, bible, outline,
  scenes, draft, synopsis) contain the update-in-place rule and the `[PENDING:` token
  guidance (or link the protocol).
- `bookwright-constitution` and `bookwright-continuity` contain `bookwright graph build --json`.

### `test_command_budget.py` — FR-015 / SC-002
- For every command body, `approx_tokens(body) < 5000`.

### `test_command_references.py` — FR-028 / FR-029 / SC-005
- `references/` dir exists and is non-empty.
- Collect every `references/<file>` path cited across the 10 bodies (regex on
  `references/...md`); assert each resolves to a shipped file (no dangling reference).
- (Soft) every shipped reference file is cited by ≥1 body (no orphan).

### `test_command_activation.py` — SC-003 backstop
- Each `description` contains at least one ES trigger and one EN trigger.
- The four sibling pairs each carry their disambiguating keyword
  (constitution↔bible, analyze↔continuity, clarify↔checklist, and the bible-not-premature signal).
- Note: this is a keyword backstop; the authoritative SC-003 check is the hand-run A/B
  battery recorded in the spec (US3).

## Out-of-scope guard — SC-007 / FR-031
- No `SKILL.md` anywhere in the diff; nothing written under `.claude/skills/` or
  `.agents/skills/`; no helper `.py` under `resources/commands/`. (Verified by diff
  inspection during review; optionally a test asserting `commands/` contains only `.md`.)

## Pass criteria
10/10 sources pass every applicable assertion; 0 dangling references; suite green under
`uv run pytest tests/resources/ -q`.
