# Quality Audit Checklist

Source: [review.md](../review.md) (7b2a3aa)

No CRITICAL or HIGH findings on this branch. The two MEDIUM/LOW findings track structural cleanup that should land before this branch merges:

- [ ] R1 — Cluster `init`'s helpers into a `commands/init/` package ([src/bookwright/commands/](../../../src/bookwright/commands/))
- [ ] R2 — Drop the `_init_envelope` lazy-import cycle workaround (auto-closed by R1) ([src/bookwright/commands/_init_envelope.py:196-200](../../../src/bookwright/commands/_init_envelope.py#L196-L200))

Historical (4b8fb4f baseline, all closed):

- [X] R1 (was) — `init.py` exceeds 500-line ceiling — closed by `c99f993`
- [X] R2 (was) — `_emit_warnings_stderr` dead code — closed by `c99f993`
- [X] R3 (was) — envelope translate dedup — closed by `c99f993`
- [X] R4 (was) — `_attach_integration_options_to_manifest` no-op — closed by `c99f993`
- [X] R5 (was) — `test_named_mode_reserved_slug` naming — closed by `c99f993`
