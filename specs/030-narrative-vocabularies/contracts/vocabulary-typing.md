# Contract: Propp/Greimas vocabulary typing

The guarantees this feature adds, as testable clauses. "Active" = the vocabulary
name appears in `manifest.vocabularies.active`. "Term" = a `crm:E55_Type`
individual in the corresponding populated TTL.

## Vocabulary data

- **C1 — Populated, valid TTL.** `propp.ttl` parses and contains exactly 31
  `crm:E55_Type` terms; `greimas.ttl` parses and contains exactly 6. Neither adds
  a class to `golem.ttl`. *(FR-001, FR-002, SC-006)*
- **C2 — Disjoint match-names.** Within each vocabulary, every term's
  `rdfs:label`s slug (`make_slug`) to values that are unique across terms; loading
  a vocabulary with a duplicate slug raises a clear data error. *(FR-011)*
- **C3 — ES + EN coverage.** Each term carries at least one `@en` and one `@es`
  label, both resolvable. *(FR-010)*

## Loader (`io/vocabularies.py`)

- **C4 — Resolve by normalized name.** `VocabularyIndex.resolve(name)` returns the
  term URI when `make_slug(name)` matches a term's label slug, else `None`; an
  unsluggable name returns `None`. *(FR-010, FR-006)*
- **C5 — Known names only.** `load_active_vocabularies` loads `propp`/`greimas`
  from the active list and ignores any other name (no error, types nothing).
  *(FR-003 edge case)*

## Function typing — Propp (G10)

- **C6 — Match ⇒ typed.** Propp active + a `functions:` name matching a Propp term
  ⇒ the `NarrativeFunction` emits `(function, crm:P2_has_type, term)` and `(term,
  rdf:type, crm:E55_Type)`. *(FR-004, SC-001)*
- **C7 — ES form ⇒ same term.** The Spanish spelling of a function name types to
  the same term as its English form (case/accent/ES-EN tolerant). *(FR-010, US1 §3)*
- **C8 — No match ⇒ untyped, no error.** A name matching no active term ⇒ the
  function is identity-only, no `P2_has_type`, build succeeds. *(FR-006, SC-001)*

## Role typing — Greimas (G11)

- **C9 — Match ⇒ typed.** Greimas active + a character card `narrative_roles:`
  name matching a Greimas actant ⇒ the character-scoped `CharacterRole` node emits
  `(role, crm:P2_has_type, term)` + `(term, rdf:type, crm:E55_Type)`. Typing
  attaches at materialization, independent of any unit card's `roles:` reference.
  A non-matching role is left untyped, no error. *(FR-005, FR-006, SC-002)*

## Provenance (FR-013)

- **C10 — Typing is reified, not bare.** Every `P2_has_type` typing link has a
  corresponding `crm:E13_Attribute_Assignment` (minted by `build_provenance` from a
  `DerivedAssertion`) whose `crm:P140_assigned_attribute_to` is the typed entity,
  `crm:P141_assigned` is the term, and `crm:P70_documents`/source locator is the
  originating card. No typing link appears as an un-provenanced triple. *(FR-013)*

## Activation gating & no-regression

- **C11 — Inactive ⇒ never typed.** With a vocabulary not in `active`, a name that
  *would* match one of its terms is not typed (no `P2_has_type`, no E13). *(FR-009)*
- **C12 — None active ⇒ identical to 028/029.** With an empty `active` list, the
  narrative-function and narrative-role graph (triples + E13 reifications) is
  byte-for-byte the pre-feature output. *(FR-008, SC-003)*
- **C13 — Stable across rebuilds.** Same source + same active vocabularies ⇒
  identical set of `P2_has_type` links and E13s every build. *(FR-011, SC-004)*

## References (SC-005)

- **C14 — References ↔ terms agree.** Each reference's "Canonical match-names"
  section enumerates exactly the EN/ES match-names of its vocabulary's terms — no
  name absent from the TTL, none in the TTL absent from the reference (both
  directions). *(FR-012, SC-005)*
