# Quickstart: Validating Release Prep (iteration 12)

**Branch**: `011-release-prep` | **Phase**: 1

This is the maintainer's walkthrough to prove the iteration is done. It is
distinct from the *user-facing* quickstart that ships in `README.es.md` /
`docs/getting-started.md` (which this iteration finalizes). Run from the
repo root with the env synced (`uv sync`).

---

## 1. Fixtures are valid Bookwright projects (US1 / SC-001)

```bash
# The fixture tests copy each fixture to a tmp dir and drive the real CLI.
uv run pytest tests/fixtures -v        # or tests/e2e if co-located
```

Expect: green. Manually spot-check `tiny-novel` (copy out first so the
committed tree stays clean — graph.ttl is derived, D2):

```bash
rm -rf /tmp/tn && cp -r tests/fixtures/tiny-novel /tmp/tn
cd /tmp/tn
uv run --project "$OLDPWD" bookwright graph build
uv run --project "$OLDPWD" bookwright graph query \
  'PREFIX golem: <...> SELECT (COUNT(?c) AS ?n) WHERE { ?c a golem:Character }' --json
uv run --project "$OLDPWD" bookwright validate --json
cd -
```

Expect: 3 characters / 2 settings / 5 events; `validate` → exit 0 / zero
`error`-severity. Repeat for `tiny-essay` and `tiny-memoir` → exit 0 / zero
`error`-severity (no non-fiction false positives; all validators active —
heuristic warnings are permitted and non-gating).

---

## 2. E2E suite passes (US2 / SC-002)

```bash
uv run pytest tests/e2e -v
```

Expect: `test_full_workflow`, `test_skills_materialization`,
`test_integration_swap` all green. The swap test asserts skills under
`.agents/skills/` and makes **no** claim about the old `.claude/skills/`.

---

## 3. Docs site builds clean (US3 / SC-004)

```bash
uv run --group docs mkdocs build --strict
```

Expect: exit 0, **zero warnings**. Then `uv run --group docs mkdocs serve`
and confirm the seven page areas (index, getting-started, architecture,
commands, validation, extending, FAQ) and one page/section per shipped
command. The architecture page summarizes and **links**
`bookwright-design.md`, not duplicates it.

Drift guard:

```bash
uv run pytest -k docs_commands_match   # documented commands == registered commands
```

---

## 4. Release metadata (US4 / SC-008)

```bash
grep -n "0.1.0" CHANGELOG.md          # v0.1.0 entry enumerating shipped features
grep -ni "integration\|validator\|vocabulary" CONTRIBUTING.md  # all three covered
test -f LICENSE && grep -n "Apache" pyproject.toml
```

Expect: CHANGELOG has a `[0.1.0]` entry listing every shipped feature;
CONTRIBUTING explains new integration + custom validator + vocabulary;
LICENSE present and referenced from metadata.

---

## 5. All quality gates green (SC-005, SC-006)

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest                          # coverage ≥ 80%, fail-closed (no round-up)
uv run pre-commit run --all-files
```

Expect: all green; reported coverage ≥ 80% (no round-up — `precision = 2`).

---

## 6. Packaged distribution validation (SC-003, SC-007 — manual)

```bash
uv build                               # → dist/bookwright_cli-*.whl + .tar.gz
pipx install ./dist/bookwright_cli-*.whl   # or: uv tool install ./dist/*.whl
cd "$(mktemp -d)"
bookwright init mi-novela --integration claude   # using ONLY the README quickstart
# … follow README.es.md: edit → graph build → graph query → validate
```

Expect: a person who has never read the source completes
init → edit → build → query → validate in ≤ 5 minutes, against the
installed CLI, without touching the source tree. Best run with an external
user (the iteration's manual-validation step).

---

## Done criteria (all must hold)

- [ ] Three fixtures present; all validate clean; tiny-novel counts = 3/2/5.
- [ ] E2E suite green and counted toward coverage.
- [ ] `mkdocs build --strict` clean; seven page areas; per-command docs.
- [ ] CHANGELOG v0.1.0, CONTRIBUTING (×3 how-tos), Apache-2.0 LICENSE.
- [ ] ruff / ruff format / mypy --strict / pre-commit / coverage > 80% green.
- [ ] Wheel builds, installs into a clean env, quickstart runs end-to-end.
