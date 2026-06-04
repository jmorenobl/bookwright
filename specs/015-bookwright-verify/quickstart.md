# Quickstart: `bookwright-verify` Skill

How to author, wire, and exercise the skill end-to-end. Run from the repo root.

## 1. Author the source command

Create `src/bookwright/resources/commands/bookwright-verify.md` per the contract
(C1–C3): YAML frontmatter (`name: bookwright-verify`, the bilingual description from
research D3) + a Spanish body with the eight sections, structurally mirroring
`bookwright-continuity.md`. Keep the description **byte-identical** to the one you
will add to `SKILL_DESCRIPTIONS` (SC-009).

## 2. Keep the four rosters in lock-step

```text
src/bookwright/integrations/descriptions.py   # + "bookwright-verify": "<same description>"
tests/integrations/test_descriptions.py       # + "bookwright-verify" in _ROSTER
tests/integrations/test_materialize.py        # + "bookwright-verify" in _ROSTER
tests/resources/helpers.py                    # + "bookwright-verify" in EXPECTED_COMMANDS
                                              #   and in REPORT_ONLY_COMMANDS
tests/resources/test_command_body.py          # add "bookwright-verify" to the
                                              #   test_graph_build_is_inline parametrize
```

(`iter_command_sources()` and the `_ROSTER`s derived from it extend automatically.)

## 3. Run the targeted gates

```bash
uv run pytest tests/resources/test_command_frontmatter.py \
              tests/resources/test_command_activation.py \
              tests/resources/test_command_body.py \
              tests/integrations/test_descriptions.py \
              tests/integrations/test_materialize.py -q
uv run ruff check && uv run ruff format --check && uv run mypy --strict
```

Expected: the inventory, frontmatter, bilingual, body-section, report-only,
inline-graph-build, and description-equality gates all pass with the new command
included.

## 4. Materialize via `init` and inspect both integrations

```bash
uv run bookwright init demo-novel --integration claude  # default
# ...and a generic-integration project to confirm both:
uv run bookwright init demo-generic --integration generic
```

Confirm a valid skill in each:

```bash
cat demo-novel/.claude/skills/bookwright-verify/SKILL.md
cat demo-generic/.agents/skills/bookwright-verify/SKILL.md
```

Each must have `name: bookwright-verify` matching its directory, the licensed
frontmatter, and `$ARGUMENTS` (not `{ARGS}`) in the body — i.e. pass `lint_skill_md`
(asserted by `test_setup_materialize` / `test_e2e_materialize`).

## 5. Exercise the skill behaviourally (manual / agent)

Against a project whose graph carries an anchor (e.g. *"private detectives were not
legally licensed in Spain before 1957"*) and a `manuscript/` scene that violates it
(a 1950 scene with a licensed PI):

1. In an agent, invoke `/bookwright-verify`.
2. The skill runs `bookwright graph build`, then `bookwright graph query` to load the
   anchors + sources, reads `manuscript/`, and reports the offending passage as a
   contradiction — quoting the passage, naming the anchor, citing the source, and
   assigning a severity (`error` for a hard anachronism). → **SC-002**.
3. Against a manuscript consistent with every anchor: zero contradictions, nothing
   invented. → **SC-003**.
4. With no manuscript: "prerrequisito ausente", points to `bookwright-draft`. With no
   anchors / `[research].enabled = false`: "nothing to verify", zero contradictions.
   → **SC-007**.
5. Trigger on both "verifica si mi manuscrito contradice lo investigado" and "check
   my manuscript against my research". → **SC-006**.
6. Confirm the working tree is unchanged after the run. → **SC-005**.

## 6. Full suite

```bash
uv run pytest         # ≥ 80% coverage gate (single-sourced); SC-008
```
