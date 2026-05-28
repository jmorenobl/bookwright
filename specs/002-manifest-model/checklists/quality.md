# Quality Audit Checklist

Source: review.md (aff10b5)

- [X] R1 — `Manifest.dump` silently drops Pydantic-side mutations: document the constraint in `contracts/manifest_api.md` §`Manifest.dump` AND add a regression test in [tests/core/test_write.py](tests/core/test_write.py) ([src/bookwright/core/manifest.py:378-411](src/bookwright/core/manifest.py#L378-L411))
- [X] R2 — US5 forward-compat is `manifest_version`-only: document the limit in `contracts/manifest_api.md` §`Manifest.load`/Classification and add a fixture asserting `extra_forbidden` fires on unknown keys inside `[bookwright]` ([src/bookwright/core/manifest.py:115-118](src/bookwright/core/manifest.py#L115-L118))
