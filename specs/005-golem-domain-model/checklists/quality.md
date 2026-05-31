# Quality Audit Checklist

Source: review.md (dbc901f) — lens: planning jargon in names

- [ ] R1 — Rename `test_us1_worked_examples` → behavior-describing name (tests/golem/test_uri.py:60)
- [ ] R2 — Strip ephemeral planning tags — user-story (`+US5`, `US5-x`, `US1`, `US2-4`, `pre-US5`) and task IDs (`T021`) — from golem docstrings/comments; keep neighbouring `FR`/`SC`/`D` refs (character.py, feature.py, __init__.py, namespaces.py, test_character_attributes.py, test_namespaces.py, test_triples.py, test_turtle_roundtrip.py, test_uri.py)
- [ ] R3 (docs, MEDIUM) — Add the trace-tag convention to CONTRIBUTING.md (allowed classes, relative resolution, freeze-on-merge). Sanctions FR/SC/D/§; forbids US/T0xx in code. No code churn.
