# Quality Audit Checklist

Source: review.md (R8-R22 cycle, audit at `4aef578`, 2026-05-29)

- [X] No CRITICAL or HIGH findings.
- [X] Coverage gate ≥ 80 % (actual: 98.02 % global; integrations layer 100 % per file).
- [X] 214 / 214 tests pass; `ruff check`, `ruff format --check`, `mypy --strict` clean.

### Closed in prior passes (history preserved)

- [X] R1 — Integration source code is untracked (closed by `7427249`)
- [X] R2 — Integration test suite is untracked (closed by `7427249`)
- [X] R3 — `tasks.md` is untracked (closed by `7427249`)
- [X] R4 — `--skills-dir` not validated for project-root containment (closed by `16d1e2f`)
- [X] R5 — `_IntegrationError.to_dict()` base body is dead code (closed by `ce048bc`; superseded by R20)
- [X] R6 — `--skills-dir` values that collapse to `project_root` itself bypass the R4 guard (closed by `c80f558`)
- [X] R7 — `parse_options` leaks bare `ValueError` from `shlex.split` on unbalanced quotes (closed by `c80f558`)

### Closed in this audit cycle (R8-R20)

- [X] R8 — `IntegrationOption.default` declared but never applied (closed by `0dd7813`)
- [X] R9 — Empty-input short-circuit bypasses `_validate_descriptor` (closed by `5dd1518`)
- [X] R10 — `Manifest.build` always triggers integrations import (closed by `ec5df13`)
- [X] R11 — `--flag=` (inline empty value) silently parses as `''` (closed by `782dd08`)
- [X] R12 — `existing is cls` defeats reload idempotency (closed by `04140aa`)
- [X] R13 — `_register` accepts `cls.key == ''` silently (closed by `bf62e1f`)
- [X] R14 — Duplicate flags in `options()` silently coalesce (closed by `231b2d2`)
- [X] R15 — `--skills-dir` and `--skills_dir` collide after normalize (closed by `33c3b5c`)
- [X] R16 — Pinned-SHA test breaks on Windows CRLF checkouts (closed by `4aef578`)
- [X] R17 — `INTEGRATION_REGISTRY` in `__all__` invited direct mutation (closed by `578abb6`)
- [X] R18 — `_IntegrationError.to_dict()` `NotImplementedError + pragma` masks forgetful subclasses (closed by `e6f79da`; superseded by R20)
- [X] R19 — `config: ClassVar[dict] = {}` shared mutable default (closed by `16a89f3`)
- [X] R20 — Five near-identical `to_dict()` overrides (closed by `7d8859a`)

### Accepted — deferred to a later milestone

- [ACCEPTED] R21 — TOCTOU race in `setup()` between `is_relative_to(root)` and `mkdir(parents=True)` — deferred to **v0.5 (extension system)** when third-party plugins enter the threat model.
- [ACCEPTED] R22 — `MalformedOptionError` covers both input-parse and path-placement errors — deferred until iteration 4's `init --json` envelope ships and consumer telemetry confirms the distinction must rise from `rule` to `code`.

### Open

None. Iteration 3 is finding-free at every severity. Ready to merge to `main` and proceed with iteration 4 (`bookwright init`).
