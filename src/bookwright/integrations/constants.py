"""Agent Skills (agentskills.io) compliance constants for the integrations layer.

Single source of truth for the numeric caps, the inherited default license,
and the dynamic-context injection allowlist consumed by iteration 9's
``SKILL.md`` materializer and linter (FR-003, FR-005, FR-013, FR-015).

Structural invariant from FR-003 — *the directory name MUST equal the
``name`` field inside its ``SKILL.md``* — is not numeric and therefore is not
encoded as a constant; it is enforced by iteration 9's materializer/linter and
documented here so future readers do not duplicate the rule.
"""

from __future__ import annotations

from typing import Final

SKILL_NAME_MAX_LENGTH: Final[int] = 64
SKILL_DESCRIPTION_MAX_LENGTH: Final[int] = 1024

#: Tier-2 ``SKILL.md`` body budget (R6/FR-015). Bodies are copied unchanged from
#: already-budget-passing iteration-8 sources, so this is a regression guard.
SKILL_BODY_MAX_TOKENS: Final[int] = 5000

#: License inherited by a materialized skill when its source declares no
#: ``license`` (FR-005/A-002). The single source of truth for the design default.
DEFAULT_SKILL_LICENSE: Final[str] = "Apache-2.0"

#: Deny-by-default allowlist of project-file *read* commands permitted inside a
#: `` !`…` `` dynamic-context injection (the FR-013 invariant). File-read only —
#: ``ls``/``find`` (which *list*, not *read a file*) are deliberately excluded to
#: stay faithful to FR-013 ("reads a project file").
INJECTION_READ_COMMANDS: Final[frozenset[str]] = frozenset({"cat", "head", "tail"})

#: DEPRECATED (iteration 9): the iteration-3 placeholder-marker filename. The
#: marker is **no longer written** — ``setup()`` now materializes real
#: ``SKILL.md`` files. Retained only so the deprecated symbol stays importable
#: for the legacy-cleanup tests; do not write this file in new code.
SKILL_PLACEHOLDER_MARKER_NAME: Final[str] = ".bookwright-skills-placeholder"
