"""Exception hierarchy for plain-text → model parsing (the ``io`` package).

Every concrete error inherits the canonical ``--json`` envelope from the shared
``BookwrightError`` base (Principle IX, data-model § 6); this module declares only
each error's ``code`` and ``details``.
"""

from __future__ import annotations

from bookwright.errors import BookwrightError


class IOError_(BookwrightError):
    """Base for every failure mode the ``bookwright.io`` package owns.

    Named with a trailing underscore so it never shadows the builtin ``IOError``.
    Abstract: declares no ``code`` and is never serialized directly.
    """


class ProjectNotFoundError(IOError_):
    """No ``manifest.toml`` was found in the cwd or any ancestor (R8)."""

    code = "not_a_project"

    def __init__(self, start: str) -> None:
        self.start = start
        super().__init__(
            f"no manifest.toml in {start} or any parent directory",
            {"start": start},
        )


class MissingDirectoryError(IOError_):
    """A required content directory (``bible/`` or ``manuscript/``) is absent (FR-012)."""

    code = "missing_directory"

    def __init__(self, name: str, path: str) -> None:
        self.name = name
        self.path = path
        super().__init__(
            f"required directory {name!r} is missing at {path}",
            {"name": name, "path": path},
        )


class InvalidFrontmatterError(IOError_):
    """A single source file's frontmatter is unusable (FR-013).

    Per-file and collected: the build skips the file, records ``(path, reason)``,
    and continues — it never aborts the whole build.
    """

    code = "invalid_frontmatter"

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(
            f"invalid frontmatter in {path}: {reason}",
            {"path": path, "reason": reason},
        )


class ResearchError(IOError_):
    """A ``bible/research/`` file is structurally invalid — fatal, no graph (D7).

    Unlike the bible mapper, which soft-skips an unusable file, research is
    validated strictly: an out-of-vocabulary ``type``/``reliability``, a missing
    required Source facet, a non-open finding lacking ``claim``/``sources``, an
    ``anchors[].promotes`` naming an unknown finding, a translation-rule violation,
    or malformed YAML aborts the build naming the offending file and value
    (FR-016). ``value`` carries the offending key or value (``None`` when the fault
    is structural rather than value-level).
    """

    code = "invalid_research"

    def __init__(self, relpath: str, message: str, value: str | None = None) -> None:
        self.relpath = relpath
        self.value = value
        super().__init__(message, {"relpath": relpath, "value": value})


class SlugCollisionError(IOError_):
    """Two entities of one concept share an identifier (FR-014) — fatal, no graph."""

    code = "slug_collision"

    def __init__(self, identifier: str, first_path: str, second_path: str) -> None:
        self.identifier = identifier
        self.first_path = first_path
        self.second_path = second_path
        super().__init__(
            f"identifier {identifier!r} is claimed by both {first_path} and {second_path}",
            {"identifier": identifier, "sources": [first_path, second_path]},
        )
