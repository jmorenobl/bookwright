# Quickstart — Validation System

Deterministic coherence checks for a Bookwright project. Run from anywhere inside
a project (the command walks up to `manifest.toml`).

## Run a validation

```bash
uv run bookwright validate
```

Runs all active validators over the bible, manuscript, constitution, and the
already-built graph (`bible/graph.ttl`, if present — run `bookwright graph build`
first to populate it). The report groups findings by validator with each
location, rule, and explanation. A clean project prints "no violations found" and
exits 0.

## Machine-readable output (CI / editors)

```bash
uv run bookwright validate --json
```

Emits one JSON document on stdout (and nothing else); progress goes to stderr.
The exit code gates CI:

- `0` — no error-severity violation,
- `1` — at least one error-severity violation,
- `2` — configuration/usage error (no project, bad manifest, unknown validator, bad scope).

`--json` carries `failed` (the gate) and a `summary`; the exit code mirrors `failed`.

## Narrow what is reported

```bash
# only findings whose source is in this chapter
uv run bookwright validate --scope manuscript/cap-04.md

# threshold: this level and above (error > warning > info)
uv run bookwright validate --severity warning      # warnings + errors
uv run bookwright validate --severity error        # errors only
```

`--scope` and `--severity` change the **display only** — they never change the exit
code. An error-severity violation always fails the run even if filtered out of the
shown report. Location-less findings (e.g. a `follows` cycle, an orphaned bible
character) are omitted under an active `--scope` and appear only in a full run.

## Built-in validators

| Validator | Severity | Checks |
|---|---|---|
| `temporal` | error | timeline contradictions in the graph over a multi-year **interval** model: `follows`/`precedes` cycles, a pair both ordered and overlapping, containment vs. strict order, and numeric begin/end contradicting a declared relation. Declare per-event `begin:`/`end:` (or `date:`) and relation keys in `bible/timeline.md` (see below), then `graph build`. |
| `character_presence` | error / warning | a bible character never mentioned in the manuscript → **error**; a proper-noun mention with no bible entry → **warning** (heuristic name matching, no NER — may flag places/orgs, so it never fails the build). |
| `setting_continuity` | warning | the same setting is not described with contradicting terms (e.g. *coastal* vs *inland*) across files. |
| `focalization` | warning | the manuscript respects the narrative person / focal character declared under "Voz narrativa" in the constitution. |

### Declaring a timeline for the `temporal` validator

In `bible/timeline.md`, events may carry an optional time **interval** and any of the
five qualitative relations (all keys optional and backward compatible):

```yaml
---
events:
  - name: "Fundación de Destilerías Ayelo"
    begin: 1885            # begin year; omit `end` for an open (begin-only) interval
    end: 1912              # end year; a single-year event can use `date: 1885` instead
    participants: ["Manuel de Aparici"]
  - name: "Quiebra de la sociedad"
    date: 1884             # shorthand for begin == end == 1884
    follows: ["Fundación de Destilerías Ayelo"]   # 1884 cannot follow [1885,1912] → temporal error
    # also available: precedes / overlaps / includes / included_in (lists of event names)
---
```

After `bookwright graph build`, `bookwright validate` reports the contradiction.
`date:` is a shorthand for a single-year (point) interval and is mutually exclusive
with `begin:`/`end:`. An unresolved relation name is a soft build warning, like an
unresolved participant.

## Configure which validators run

In `manifest.toml`:

```toml
[validators]
enabled  = []                 # empty = all built-ins; e.g. ["temporal","character_presence"] = only these
disabled = ["focalization"]   # remove specific validators
custom   = []                 # empty = all discovered customs; non-empty = allow-list
```

Naming a validator that does not exist is an error (exit 2), not a silent no-op.

## Add a custom validator

Drop a `.py` file into `<project>/.bookwright/validators/`:

```python
# .bookwright/validators/no_todo.py
from bookwright.validation import Severity, Violation

class NoTodoMarkers:
    name = "no_todo"
    severity_default = Severity.warning

    def validate(self, project, indexer):
        out = []
        for relpath, text in project.manuscript_files():
            for i, line in enumerate(text.splitlines(), start=1):
                if "TODO" in line:
                    out.append(Violation(
                        validator=self.name, severity=self.severity_default,
                        message="leftover TODO marker in prose",
                        source=f"{relpath}:{i}", triples=(),
                    ))
        return out
```

It is discovered and run on the next `bookwright validate` alongside the built-ins.
A malformed custom file is skipped with an attributed message (shown under
`errors`) and never crashes the run. Custom validators run with project-level
trust (no sandboxing in v0).
