# Quality Audit Checklist

Source: review.md (a3db7f1)

- [ ] R1 — Commit (or revert) all iteration-2 work product before claiming close (`src/bookwright/core/`, `src/bookwright/resources/`, `tests/core/`, plus the modified `constitution.md` / `pyproject.toml` / `uv.lock` / `tasks.md`)
- [ ] R2 — Decompose `src/bookwright/core/manifest.py` (562 LoC) below the 500-line cap; extract `_translate.py` and `_build.py`
- [ ] R3 — Re-stage `tasks.md` so the `[X]` flips appear in the same push as the commits that prove each task done
- [ ] R4 — Commit the constitutional amendment + `pyproject.toml` + `uv.lock` as the first commit of the implementation push, satisfying the plan's "amendment must land before implementation" gate
- [ ] R5 — `Manifest.dump` silently drops Pydantic-side mutations; document the constraint in `contracts/manifest_api.md` and add a regression-locking negative test
