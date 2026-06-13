# Data Model: Skills Status Integration

*No new domain entities are introduced in this iteration.*

The integration logic operates purely on the `SkillsIntegration` class and the `generate_skill_md` flow, reading the state of `supports_dynamic_context` to format the materialized markdown strings.

- `Integration.supports_dynamic_context` (boolean): Flag dictating whether the `claude` (dynamic `!bookwright status --json`) or `generic` (explicit run instruction) injection is applied.
