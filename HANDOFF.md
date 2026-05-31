# HANDOFF — complete iteration 5 (GOLEM character attributes), then resume iteration 6

> Transient working note for a fresh session. Not part of any spec. Delete once
> iteration 5's model extension is merged to `main` and iteration 6 resumes.
> You are on branch `005-golem-domain-model` (pre-flight already done).

## Why this exists

Planning iteration 6 (graph indexer) surfaced that iteration-5's GOLEM model —
already merged to `main` — is **identity-only**: `Character` carries only
`name` + `uri_base` and emits just an `rdf:type` triple. It cannot represent the
documented character frontmatter (`born`, `died`, `features[]`,
`narrative_roles[]`) that iteration 6 must turn into triples (and that iteration
10's temporal / character-presence validators will need). Iteration 5 was
under-scoped; the fix belongs here, at the model layer — not patched inside
iteration 6.

## The decision (frozen terms only — drop nothing, mint nothing)

The frozen `src/bookwright/resources/schemas/golem-1.1/golem.ttl` already defines
a home for every documented key, so SC-001 ("zero classes/predicates outside the
frozen vocabulary") holds:

| Frontmatter | Frozen GOLEM/CIDOC modeling |
|---|---|
| `name` | identity (slug → URI) + `rdf:type golem:G1_Character` (already done) |
| `narrative_roles[]` | `Character —dlp:plays→ golem:G11_Narrative_Role` |
| `features[]` (free text) | `Character —gc:GP0_has_feature→ golem:G17_Character_Feature`; text via `rdfs:label` |
| `born` / `died` (year) | biographical `golem:G17_Character_Feature`, `crm:P2_has_type` an `crm:E55_Type` individual (birth/death), year via `crm:P43_has_dimension → crm:E54_Dimension —crm:P90_has_value→ "YYYY"^^xsd:gYear` |

⚠️ **Namespace trap:** `plays`/`played-by`/`uses`/`setting` live in
`http://www.ontologydesignpatterns.org/ont/dlp/ExtendedDnS.owl#`, **not** the
existing `DLP` constant in `namespaces.py` (`…/DOLCE-Lite.owl#`, which is where
`participant`/`proper-part`/etc. correctly come from). Add a new namespace
constant (e.g. `EDNS`) + a bound prefix.

The full rationale + draft modeling already lives on the **`006`** branch:
```
git show 006-graph-indexer:specs/006-graph-indexer/research.md       # R1 + R1a
git show 006-graph-indexer:specs/006-graph-indexer/data-model.md     # §0 model extension
git show 006-graph-indexer:specs/006-graph-indexer/contracts/bible-format.md
```
Migrate that content into the 005 artifacts.

## Spec Kit runbook (amend 005 in place)

1. Sanity: `.specify/scripts/bash/setup-plan.sh --json` → `SPECS_DIR` must end in
   `005-golem-domain-model`. (`.specify/feature.json` gates this and overrides the
   branch name.)
2. **Do NOT run `/speckit-specify`** — its mandatory `before_specify` hook creates
   a *new* branch. Instead, edit `specs/005-golem-domain-model/spec.md` directly
   (add a functional requirement for the character-attribute mapping above, with
   acceptance scenarios).
3. `/speckit-clarify` — lock the `born`/`died` modeling depth (the
   `E54_Dimension`/`P90_has_value` chain; minting `E55_Type` birth/death
   individuals at stable URIs).
4. `/speckit-plan` — hint: *"Extend the GOLEM typed model: new `CharacterFeature`
   (G17) + `Dimension` (E54) in `golem/modules/feature.py`; `Character.features`/
   `.roles` fields + cross_refs; new predicate constants + ExtendedDnS namespace
   in `namespaces.py`. Additive — keep identity-only behaviour and existing tests;
   extend the closure test."*
5. `/speckit-tasks` — tell it iteration-5's identity-only work is **done and
   merged**; the new tasks are **additive** (don't replan iter 5 from scratch).
6. `/speckit-analyze` — fix anything flagged.
7. `/speckit-implement`, then green every gate:
   ```
   uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy --strict src tests
   ```
8. Accept the optional commit hooks between phases (checkpoints → clean ff-merge).

## Finish & return to iteration 6

```bash
git switch main && git merge --ff-only 005-golem-domain-model
git switch 006-graph-indexer && git rebase main
```
Then on `006`: drop R1a from its artifacts (the richer model is now a plain
dependency on `main`, like the iteration-2 `Manifest`) and resume at
`/speckit-tasks`.

## Not in this 005 flow

Iteration 6 separately needs `pyyaml>=6.0` added to runtime deps (frontmatter
parsing) = a Principle-II **MINOR** constitution amendment
(`/speckit-constitution`, 1.1.0 → 1.2.0) + a design § 14.1 update. Do that on the
`006` branch, **not** here — extending the GOLEM model adds no runtime dependency.
