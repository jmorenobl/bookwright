# Quality Audit Checklist

Source: [review.md](../review.md) (1c6ad45 → 0adb89f)

- [X] No CRITICAL or HIGH findings on this branch.
- [X] R1 MEDIUM — share one `SkillsIntegration` instance across `main.run` + `run_scaffold_steps` (closed in `0adb89f`).
- [X] R2 LOW — delete dead-code `if False else None` in `tests/commands/test_init_options_record.py` (closed in `0adb89f`).
- [X] R3 LOW — rename `test_named_mode_reserved_slug` to `test_named_mode_slugifies_to_empty` (closed in `0adb89f`).
- [X] R4 LOW — collapse `import os as _os  # noqa: PLC0415` to top-level `import os` across the test grid (closed in `0adb89f`).
- [X] Contract §5 / FR-032 — warnings emitted to stderr regardless of `--json` (surfaced by `/simplify`, closed in `0adb89f`).
