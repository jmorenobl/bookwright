# Contract: Fixture Project Shape

**Branch**: `011-release-prep` | **Phase**: 1 | Maps to FR-001…FR-005, SC-001

Each fixture under `tests/fixtures/<name>/` is a **finished** minimal
Bookwright project: initializable, graph-buildable, queryable, validatable,
and clean (exit 0 / zero `error`-severity violations) in its shipped state. Plain text only — no
committed `bible/graph.ttl`, no materialized skills dir (D2, D9).

A fixture-level test module (`tests/fixtures/test_fixtures.py` or under
`tests/e2e/`) enforces this contract by copying each fixture to `tmp_path`
and running the real CLI.

---

## tiny-novel (FR-001)

```
manifest.toml          [book] type = novel; [validators] all built-ins active
bible/constitution.md  declares a narrative voice consistent with the chapter
bible/characters/       EXACTLY 3 files, each: name (+ optional born/features/
                        narrative_roles), all mentioned in the manuscript
bible/settings/         EXACTLY 2 files, each: name
bible/timeline.md       events: list of EXACTLY 5 items {name, participants:[slug…]}
                        every participant slug resolves to a character file
outline/*               fully populated (synopsis, structure, arcs, scenes)
manuscript/<chapter>.md 1 draft chapter; names every character at least once
```

**Asserted (SC-001 / VR-1, VR-2, VR-3, VR-6)**:
- `graph build`: exit 0, 0 skips, 0 unknown_keys.
- `graph query`: exactly **3 Character, 2 Setting, 5 NarrativeEvent**.
- `validate`: **exit 0 / zero `error`-severity** (heuristic warnings non-gating).

---

## tiny-essay (FR-002)

```
manifest.toml          [book] type = "essay"; ALL built-in validators active
                       ([validators] disabled = [])   (revised D3)
bible/                 NO characters/ entries (no fictional characters)
manuscript/            3 chapters
bibliography           a bibliography document (e.g. bible/research.md or
                       a references file) — present and coherent
```

**Asserted (FR-002, VR-3, edge case "non-fiction false positives")**:
- `graph build`: exit 0, clean.
- `validate`: **exit 0 / zero `error`-severity** — with all validators
  active, `character_presence` yields only warnings (empty roster → no
  orphan error) and `focalization` is silent (no third-person declaration),
  so no false-positive *error* occurs.

---

## tiny-memoir (FR-003)

```
manifest.toml          [book] type = "memoir"; ALL built-in validators active
                       ([validators] disabled = [])
bible/characters/      EXACTLY 1 protagonist = the author
bible/constitution.md  first-person voice declaration → focalization stays silent
manuscript/            autobiographical scenes/chapters that mention the author
```

**Asserted (FR-003, VR-3)**:
- `graph build`: exit 0, clean; the single protagonist present.
- `graph query`: the single protagonist and the autobiographical scenes
  are in the index.
- `validate`: **exit 0 / zero `error`-severity** (warnings non-gating).

---

## Shared invariants (all fixtures)

| ID | Rule |
|----|------|
| F1 | Locatable by `find_project_root` (has `manifest.toml`). |
| F2 | `graph build` → 0 skips, 0 unknown_keys (authored to iter-6 mapper keys). |
| F3 | `validate` → exit 0 / zero `error`-severity in shipped state; heuristic warnings permitted (FR-004). |
| F4 | No `[PENDING: …]` sentinel in any author-fill section (VR-4). |
| F5 | Plain text only; no `graph.ttl`, no skills dir committed (VR-5, D2). |
| F6 | Coherent, not rich — minimal prose, internally consistent (Assumptions). |

A *violating* variant (for negative tests) is derived in `tmp_path` by
injecting an inconsistency into a copy — never committed as a second fixture.
