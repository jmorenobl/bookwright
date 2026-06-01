# Contract: Skeleton ↔ iter-4 `init` Walker

**Direction**: templates → consumer. The iter-4 walker is frozen (FR-023);
skeleton files under `resources/project/` MUST conform to it. Authoritative
source:
[`src/bookwright/commands/init/scaffold.py`](../../../src/bookwright/commands/init/scaffold.py)
(`render_resource_tree`, `_target_relpath`, `run_scaffold_steps`).

## W1. Extension semantics

- A file ending in `.j2` is rendered through one shared
  `jinja2.Environment(undefined=StrictUndefined, autoescape=False,
  keep_trailing_newline=True)`; the `.j2` suffix is stripped from the stamped
  name (`_target_relpath`).
- **Every other file is byte-copied verbatim**, suffix intact. Therefore a
  `*.tmpl` placed under `project/` would be stamped literally as `*.tmpl` into
  the new project — forbidden (spec edge). Molds live only under
  `resources/templates/`.
- Skeleton singletons therefore use `.md` or `.j2` — never `.tmpl`.

## W2. Available Jinja2 context (the only legal variables)

`render_resource_tree` is called with exactly:

| Variable | Source |
|---|---|
| `title` | resolved project title |
| `project_slug` | resolved slug |
| `author` | `resolved.authors[0]` |
| `language` | resolved language |
| `integration_key` | resolved integration key |

`StrictUndefined` means any other `{{ var }}` raises at render → `init` aborts
and rolls back. Design § 9.2's `{{ book.title }}` is **not** available; use
`{{ title }}`. Files touched: `constitution.md.j2`, `README.md.j2`.

## W3. Directory & marker preservation

The walker preserves empty directories via `.gitkeep` resources. This iteration
does **not** add or remove directories: `bible/characters/.gitkeep` and
`bible/settings/.gitkeep` remain (they are the stamp destinations for filled
character/setting instances). No `.tmpl` is introduced under `project/`.

## W4. Atomicity is the walker's concern, not ours

Each write goes through the backup ledger (`write_bytes_atomic`); a render error
on any `.j2` rolls the whole `init` back. The contract obligation on *this*
iteration is simply: every `.j2` must render cleanly under the W2 context, so
the walker never has cause to roll back.

## W5. Verification

`tests/resources/test_skeleton_renders.py` renders every `.j2` under
`resources/project/` with a representative W2 context using the same
`jinja2.Environment` settings (or by invoking `render_resource_tree` into a temp
dir) and asserts no `UndefinedError`; `test_no_stub_sentinels.py` asserts the
stamped tree contains no sentinel (FR-022).
