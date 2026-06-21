# ruff: noqa: E501
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
DEFAULT_SKILL_LICENSE: Final[str] = "EUPL-1.2"

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

#: Stable headings prefixing the two injected blocks. Idempotency gates on these
#: sentinel markers — not the full prose — so a re-run never double-injects even if the
#: surrounding copy is later reworded (R1). The block bodies below interpolate them, so
#: the literal heading text lives here exactly once.
STATUS_INJECTION_HEADING: Final[str] = "## Orientación inicial"
NEXT_STEPS_HEADING: Final[str] = "## Próximos pasos"

#: Shared shape of the status-orientation block. Only the lead sentence and the
#: status-command rendering differ between integrations, so they are the sole
#: ``{lead}``/``{invocation}`` slots — the heading and the halt/empty-state bullets
#: live here once, keeping the Claude and Generic variants in sync by construction.
_STATUS_INJECTION_TEMPLATE: Final[str] = (
    STATUS_INJECTION_HEADING
    + """

{lead}

{invocation}

- Si el comando falla o devuelve un JSON inválido, **DETENTE INMEDIATAMENTE (halt)** y pide al usuario que corrija el error.
- Si el estado está vacío (no hay foco ni siguientes acciones), simplemente ignóralo y continúa normalmente.
"""
)

#: Status injection pattern for Claude integration (dynamic context)
STATUS_INJECTION_CLAUDE: Final[str] = _STATUS_INJECTION_TEMPLATE.format(
    lead="Antes de empezar, debes entender el estado actual del proyecto. Analiza el siguiente estado:",
    invocation="!`bookwright status --json`",
)

#: Status injection pattern for Generic integration (explicit step)
STATUS_INJECTION_GENERIC: Final[str] = _STATUS_INJECTION_TEMPLATE.format(
    lead="Antes de empezar, ejecuta el siguiente comando para entender el estado actual del proyecto:",
    invocation="```bash\nbookwright status --json\n```",
)

#: Next steps boilerplate appended at the end of skills.
NEXT_STEPS_BOILERPLATE: Final[str] = (
    "\n"
    + NEXT_STEPS_HEADING
    + """

- Revisa las acciones pendientes (`next_actions`) que obtuviste en la orientación inicial.
- Propón al usuario los comandos listos para copiar y pegar para continuar con la siguiente acción lógica.
"""
)
