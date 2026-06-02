# Quickstart: Authoring & validating a command source

How to author one of the 10 command sources and confirm it passes the gate. This iteration
ships **documents** — there is nothing to `uv run` except the validation suite.

## 1. Author the source

Create `src/bookwright/resources/commands/<name>.md`. Start from `bookwright-design.md`
§ 10.1 and adapt to the command's § 10.4 row. Skeleton:

```markdown
---
name: bookwright-<name>
description: <ES trigger> / <EN trigger>. <sibling-disambiguating clause>. (< 1024 chars)
---

# /bookwright-<name>

Eres <rol del agente>.                         # 1. Rol / contexto

## Input                                        # 2. Input esperado
{ARGS}   <!-- y el argumento posicional <scene_id>/<artifact> si aplica -->

## Procedimiento                                # 3. Procedimiento (numerado)
1. Lee <archivos a leer concretos>.
2. ...
3. (si necesita grafo) Ejecuta `bookwright graph build --json` y usa el JSON.

## Output                                       # 4. Output esperado

## Archivos a leer                              # 5.
- bible/constitution.md
- ...

## Archivos a escribir                          # 6.  (o: "Solo lectura — no escribe nada")
- bible/<...>

## Información faltante                          # 7.
Sigue `references/pending-protocol.md`: marca `[PENDING: …]` y continúa; detente solo si...

## Qué NO hacer                                  # 8.
- ...
```

Generative commands additionally state the **update-in-place** rule and link
`references/pending-protocol.md`. Report-only commands state "no escribe nada".

## 2. Add any new reference it cites

If the body links `references/<topic>.md`, create that file (Spanish prose) under
`src/bookwright/resources/commands/references/`. Never cite a reference you do not ship
(FR-029).

## 3. Keep within budget

Body < 5000 tokens (≈ < 20 000 chars; aim ≤ ~14 000). Offload domain depth to
`references/` rather than inlining it.

## 4. Validate

```bash
uv run pytest tests/resources/ -q          # full resource-validation suite (iter7 + iter8)
uv run pytest tests/resources/test_command_frontmatter.py tests/resources/test_command_budget.py -q
uv run ruff check && uv run ruff format --check
uv run mypy --strict src tests
```

Green = the format gate (FR-030) passes. Then hand-run the SC-003 activation A/B battery
(US3 scenarios, ES+EN) and read `bookwright-constitution.md` end-to-end (SC-004).

## Definition of done (this iteration)
- 10/10 sources at the prescribed paths pass the suite (SC-001).
- Every body < 5000 tokens, every description < 1024 chars (SC-002).
- 0 dangling references (SC-005); 8/8 activation phrasings resolve correctly (SC-003).
- 0 out-of-scope artifacts: no SKILL.md, no `skills_dir` writes, no helper `.py` (SC-007).
