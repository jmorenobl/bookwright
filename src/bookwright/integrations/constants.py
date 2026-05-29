"""Agent Skills (agentskills.io) compliance constants for the integrations layer.

Single source of truth for the two numeric caps and the placeholder marker
filename consumed by iteration 9's `SKILL.md` materializer (FR-033, FR-034).

Structural invariant from FR-033 — *the directory name MUST equal the
`name` field inside its `SKILL.md`* — is not numeric and therefore is not
encoded as a constant; it is enforced by iteration 9's materializer and
documented here so future readers do not duplicate the rule.
"""

from __future__ import annotations

from typing import Final

SKILL_NAME_MAX_LENGTH: Final[int] = 64
SKILL_DESCRIPTION_MAX_LENGTH: Final[int] = 1024
SKILL_PLACEHOLDER_MARKER_NAME: Final[str] = ".bookwright-skills-placeholder"
