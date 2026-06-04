"""Public API for the Bookwright core domain model.

The members re-exported below are the stable iteration-2 contract; anything
else is implementation detail. See specs/002-manifest-model/contracts/manifest_api.md.
"""

from bookwright.core._research_block import ResearchBlock
from bookwright.core.errors import (
    ManifestError,
    ManifestNotFoundError,
    ManifestOverwriteError,
    ManifestSyntaxError,
    ManifestValidationError,
    ManifestWarning,
)
from bookwright.core.manifest import (
    BOOK_STATUSES,
    BOOK_TYPES,
    KNOWN_MANIFEST_VERSIONS,
    Manifest,
)

__all__ = [
    "BOOK_STATUSES",
    "BOOK_TYPES",
    "KNOWN_MANIFEST_VERSIONS",
    "Manifest",
    "ManifestError",
    "ManifestNotFoundError",
    "ManifestOverwriteError",
    "ManifestSyntaxError",
    "ManifestValidationError",
    "ManifestWarning",
    "ResearchBlock",
]
