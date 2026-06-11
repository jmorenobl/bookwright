# Phase 1 Data Model: Authored focus state

One new entity — the **focus state** — modelled as an optional manifest block.
No graph/RDF entities are introduced (those belong to iteration 020 `status`).

## Entity: `FocusBlock`

The author's current working intent, persisted as the optional `[focus]` block in
`manifest.toml`. Module: `src/bookwright/core/_focus_block.py` (extracted to keep
`manifest.py` under the Principle IV 500-line ceiling, mirroring
`_research_block.py`). Re-exported from `bookwright.core`.

```python
class FocusBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    target: str
    notes: str = ""
    updated_at: str
```

### Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `target` | `str` | yes (when block present) | — | Short text naming what is being worked on now (e.g. `"arco de Berlín"`, `"cap-04"`). Must be non-empty / non-whitespace. |
| `notes` | `str` | no | `""` | Free-text log of open threads and pending decisions. Empty string when none. |
| `updated_at` | `str` | yes (when block present) | — | ISO 8601 calendar date `YYYY-MM-DD` (no time/timezone). CLI stamps it on every write; validated on load. |

### Attachment to `Manifest`

```python
class Manifest(BaseModel):
    ...
    focus: FocusBlock | None = None   # absent block ⇒ None
```

`None` is the canonical encoding of "no `[focus]` block" — it lets
`show --json` emit `{"status":"ok","focus":null}` (FR-005) and lets `target`/
`updated_at` be *required when present* without a misleading defaulted block
(see research D1).

### Validation rules

| Rule | Field | Behaviour | Requirement |
|---|---|---|---|
| Non-empty target | `target` | Reject empty/whitespace-only; `PydanticCustomError("empty", …)` → `focus.target` failure. | FR-008, FR-012 |
| String target | `target` | Non-string ⇒ `string_type` → `not_a_string`. | FR-012 |
| String notes | `notes` | Non-string ⇒ `not_a_string`. | FR-012 |
| ISO date shape | `updated_at` | Must match `^\d{4}-\d{2}-\d{2}$`; else `PydanticCustomError("not_iso_date", …)`. | FR-001, FR-011 |
| Valid calendar date | `updated_at` | Must parse via `date.fromisoformat`; impossible dates rejected. | FR-011 |
| Unknown key | (any) | `extra="forbid"` ⇒ `extra_forbidden` → `unknown_key`. | (block hygiene) |
| Optional block | (whole) | Absent `[focus]` ⇒ `focus is None`; never an error. | FR-002, FR-005 |

All failures flow through the existing `_translate_validation_error` →
`ManifestValidationError` (`code = "manifest_validation"`), so focus errors are
reported identically to every other manifest field error — no new error surface
on load (FR-011, Assumptions).

> **Note on empty-target enforcement.** The command (`focus set`) rejects an
> empty `--target` *before* constructing a `FocusBlock` (so the manifest is left
> unchanged, FR-008) via `FocusTargetEmptyError`. The model-level non-empty rule
> is the second line of defence covering a hand-edited manifest.

## State transitions (the `[focus]` block lifecycle)

```
            focus set --target T [--notes N]
   (absent) ───────────────────────────────────▶ (present: target=T, notes=N|"", updated_at=today)
      ▲  │                                              │  ▲
      │  │ focus set --target T  (no --notes)           │  │ focus set --target T2 [--notes …]
      │  │  → create with notes=""                      │  │  → target:=T2; notes per partial rule; updated_at:=today
      │  └──────────────────────────────────────────────┘  │
      │                                                     │
      │ focus clear                                         │
      └─────────────────────────────────────────────────────┘
                       (present) ──▶ (absent)
```

**Partial-`notes` rule on update (FR-007)** — applied by the command, then handed
to `Manifest.set_focus` as a resolved string:

| `--notes` argument | Block absent (create) | Block present (update) |
|---|---|---|
| omitted | `notes = ""` | `notes` preserved (existing value) |
| `--notes "X"` | `notes = "X"` | `notes = "X"` |
| `--notes ""` | `notes = ""` | `notes = ""` (cleared) |

In every `set` case, `target` and `updated_at` are (re)written.

**`clear` (FR-010)**: present → absent (remove block, preserve rest of manifest);
absent → absent (no-op, success).

## Mutating-API surface on `Manifest`

Two new methods, alongside `set_integration`/`dump`; both require a
document-backed instance (`load`/`build`) and mutate model + `tomlkit` document
together to preserve comments and ordering (FR-009, SC-002).

| Method | Signature | Effect |
|---|---|---|
| `set_focus` | `(*, target: str, notes: str, updated_at: str) -> None` | Create or update the `[focus]` table; refresh model `self.focus`. |
| `clear_focus` | `() -> None` | Remove the `[focus]` table if present; set `self.focus = None`. No-op when already absent. |

> **Write-shape decisions (deliberate, not incidental).**
> 1. `set_focus` always writes the `notes` key, including `notes = ""` on a create
>    with no `--notes`. The empty string round-trips and the model defaults `notes`
>    to `""` on load, so an explicit empty key and an omitted key are equivalent —
>    the explicit form is chosen for an unambiguous, greppable block.
> 2. `target` is stored **verbatim** as the author typed it (Principle I); only an
>    *empty-after-strip* value is rejected (FR-008). Leading/trailing whitespace in
>    an otherwise non-empty `target` is preserved, never trimmed.

## Backward compatibility

An existing v0.2 manifest with no `[focus]` block loads with `focus is None` and
every other command behaves identically (FR-002, SC-004). The block is additive;
`manifest_version` does **not** change (no incompatible format change).
