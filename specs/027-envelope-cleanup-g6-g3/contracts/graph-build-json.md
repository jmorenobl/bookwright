# Contract: `graph build --json` renamed key (US3, FR-015…FR-019)

The single deliberately-changed observable byte of the whole iteration.

## Change

| Aspect | Before | After |
|---|---|---|
| `--json` key | `"unresolved_participants"` | `"unresolved_references"` |
| key position | between `"unknown_keys"` and `"sources"` | **same** |
| item shape | `{"path","entity","name"}` | **same** |
| report type | `UnresolvedParticipant` | `UnresolvedReference` |
| stderr summary | `"N unresolved participant reference(s)"` | `"N unresolved reference(s)"` |
| soft-warning semantics | never changes exit code | **same** |

## Item shape (unchanged)

```json
{"path": "bible/characters/x.md", "entity": "Event Name", "name": "Unknown Ref"}
```

An item is emitted when a `participants:` member **or** a location's `setting:`
matches no built entity. The owning entity is still built.

## Acceptance

1. Build a graph over a fixture producing (a) an unresolved `setting:` and
   (b) an unmatched `participants:` reference. `graph build --json` carries
   `unresolved_references` (not `unresolved_participants`) at the same envelope
   position; each item keeps `{path, entity, name}`. (FR-016)
2. Every other byte of the envelope (key order, separators, trailing newline,
   all other field values) is identical to the pre-027 document. A new golden
   baseline replaces the old for this key only. (FR-017)
3. The stderr summary reads `"N unresolved reference(s)"`. (FR-018)
4. `grep -rn "UnresolvedParticipant\|unresolved_participants" src/ docs/` returns
   nothing; `docs/commands/graph-build.md` names `unresolved_references`. (FR-019,
   SC-007)

## Documented as

CHANGELOG entry at release (`v0.3.4`): "`graph build --json`: renamed the
`unresolved_participants` key to `unresolved_references` (now also covers
unresolved `setting:` locations); item shape unchanged."
