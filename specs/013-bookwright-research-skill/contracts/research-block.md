# Contract: `[research]` manifest block

The TOML ⇄ Pydantic contract for the optional `[research]` block. Authoritative
model: `bookwright.core.ResearchBlock` (in `core/_research_block.py`), reached
through `Manifest.research`.

## TOML surface (scaffolded form — FR-014a)

```toml
[research]
# Whether the research system is active. When false, the bookwright-research
# skill reports the system inert and produces no graph-bound findings.
enabled = true
# Source provenances (ISO 639-1 codes) the protocol should deliberately seek for
# nationally-charged topics, e.g. ["de", "pl", "en", "fr"]. Empty = no declared
# preference; the original-language rule still applies.
source_languages = []
# Minimum source reliability required before a finding may become a binding
# anchor: one of "alta" | "media" | "baja".
min_reliability_for_anchor = "media"
```

Comments MUST survive a `load() → dump()` round-trip (tomlkit; SC-002).

## Pydantic surface

```python
class ResearchBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    enabled: bool = True
    source_languages: list[str] = Field(default_factory=list)
    min_reliability_for_anchor: Literal["alta", "media", "baja"] = "media"
```

`Manifest.research: ResearchBlock = Field(default_factory=ResearchBlock)`.

## Behavioral contract

| ID | Given | When | Then |
|---|---|---|---|
| RB-1 | manifest with `[research]` block | `Manifest.load` | `.research` exposes `enabled`, `source_languages`, `min_reliability_for_anchor` (US2-IT) |
| RB-2 | manifest with **no** `[research]` block | `Manifest.load` | succeeds; defaults `True` / `[]` / `"media"` applied (FR-012, US2-2) |
| RB-3 | `min_reliability_for_anchor = "altísima"` | `Manifest.load` | `ManifestValidationError` naming `research.min_reliability_for_anchor` (FR-013, US2-3) |
| RB-4 | `source_languages = ["de", "zz"]` | `Manifest.load` | error naming `research.source_languages[1]` (`"zz"` not ISO 639-1) (FR-016) |
| RB-5 | `[research] enabled = false` | `Manifest.load` | `.research.enabled is False` (US2-1) |
| RB-6 | `[research] foo = 1` (unknown key) | `Manifest.load` | `extra="forbid"` → validation error naming the unknown key |
| RB-7 | scaffolded manifest from `init` | `load → dump → load` | the three comment lines + values persist byte-stable (FR-014a, SC-002) |
| RB-8 | the `Literal` args | unit test | equal `set(golem.namespaces.RELIABILITY_IRI)` — anti-drift (no `golem` import in `core`) |

## Non-goals

- No CLI verb reads or mutates `[research]` in this iteration.
- `_BUILD_OVERRIDE_ALLOWLIST_TABLE` gains **no** research entry: `init` writes
  the template defaults, never an override.
- The reliability **ordering** used for anchor promotion (`alta > media > baja`)
  is applied by the skill/agent (FR-015), not by this block; the block only
  supplies the threshold string.
