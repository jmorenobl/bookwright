"""``parse_options`` contract (FR-016..FR-021, SC-005)."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

import pytest

from bookwright.integrations import (
    ClaudeIntegration,
    GenericIntegration,
    IntegrationOption,
    InvalidOptionDeclarationError,
    MalformedOptionError,
    SkillsIntegration,
    UnknownOptionError,
    parse_options,
)

# ---------- happy-path table ----------


@pytest.mark.parametrize(
    "raw,expected",
    [
        # R8 — GenericIntegration declares `--skills-dir` with
        # `default='.agents/skills'`; the default fills the dict on empty
        # input so downstream consumers always see an explicit value.
        (None, {"skills_dir": ".agents/skills"}),
        ("", {"skills_dir": ".agents/skills"}),
        ("   ", {"skills_dir": ".agents/skills"}),
        ("--skills-dir .cursor/skills", {"skills_dir": ".cursor/skills"}),
        ("--skills-dir=.cursor/skills", {"skills_dir": ".cursor/skills"}),
        ('--skills-dir "path with spaces/skills"', {"skills_dir": "path with spaces/skills"}),
        # FR-017 — for a string-typed option, the next token (even if it
        # starts with `--`) is the value.
        ("--skills-dir --foo", {"skills_dir": "--foo"}),
    ],
)
def test_happy_paths_generic(
    raw: str | None,
    expected: dict[str, str | bool],
) -> None:
    assert parse_options(raw, GenericIntegration) == expected


# ---------- claude (no declared options) ----------


def test_claude_no_options_empty_input_returns_empty_dict() -> None:
    assert parse_options(None, ClaudeIntegration) == {}
    assert parse_options("", ClaudeIntegration) == {}


def test_claude_rejects_any_flag() -> None:
    with pytest.raises(UnknownOptionError) as exc_info:
        parse_options("--skills-dir x", ClaudeIntegration)
    payload = exc_info.value.to_dict()
    assert payload["integration"] == "claude"
    assert payload["value"] == "--skills-dir"
    assert payload["valid"] == []


# ---------- generic error paths ----------


def test_unknown_flag_lists_valid_alphabetic() -> None:
    with pytest.raises(UnknownOptionError) as exc_info:
        parse_options("--bogus x", GenericIntegration)
    payload = exc_info.value.to_dict()
    assert payload["integration"] == "generic"
    assert payload["value"] == "--bogus"
    assert payload["valid"] == ["--skills-dir"]


def test_missing_value_for_string_option() -> None:
    with pytest.raises(MalformedOptionError) as exc_info:
        parse_options("--skills-dir", GenericIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "missing_value"
    assert payload["value"] == "--skills-dir"


def test_inline_empty_value_for_string_option_raises_missing_value() -> None:
    """R11 — `--flag=` (inline empty) is symmetric with bare `--flag`."""

    with pytest.raises(MalformedOptionError) as exc_info:
        parse_options("--skills-dir=", GenericIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "missing_value"
    assert payload["value"] == "--skills-dir"


def test_duplicate_flag_rejected() -> None:
    with pytest.raises(MalformedOptionError) as exc_info:
        parse_options("--skills-dir a --skills-dir b", GenericIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "duplicate_flag"
    assert payload["value"] == "--skills-dir"


# ---------- R7 — shlex tokenization errors surface as MalformedOptionError ----------


@pytest.mark.parametrize(
    "raw",
    [
        '--skills-dir "unclosed',
        "--skills-dir 'unclosed",
        '"',
        "'",
    ],
)
def test_unbalanced_quotes_raise_structured_malformed_option(raw: str) -> None:
    """R7 — `shlex.split` raises bare `ValueError` on unbalanced quotes; the
    parser MUST translate this into the structured-error contract (FR-035).

    Iteration 4's `--json` envelope reads `to_dict()` directly; a leaked
    `ValueError` would leave it without a `code`/`message` payload.
    """

    with pytest.raises(MalformedOptionError) as exc_info:
        parse_options(raw, GenericIntegration)
    payload = exc_info.value.to_dict()
    assert payload["code"] == "malformed_option"
    assert payload["rule"] == "malformed_shell_syntax"
    # The raw user input is carried in `value` (not a single flag) so the
    # caller can echo the offending string back to the user.
    assert payload["value"] == raw


# ---------- FR-019 — flag-typed option must NOT swallow a following token ----------


class _FakeFlagIntegration(SkillsIntegration):
    """In-test stub that declares one ``type='flag'`` option."""

    key: ClassVar[str] = "fake-flag"
    default_skills_dir: ClassVar[str] = ".fake/skills"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [IntegrationOption(flag="--my-flag", type="flag")]


def test_flag_option_does_not_consume_following_dash_dash_token() -> None:
    """FR-019 — flag options never swallow the next token, even if it isn't a known flag."""

    with pytest.raises(UnknownOptionError) as exc_info:
        parse_options("--my-flag --foo", _FakeFlagIntegration)
    payload = exc_info.value.to_dict()
    assert payload["value"] == "--foo"
    assert payload["valid"] == ["--my-flag"]


def test_flag_option_with_inline_value_raises_unexpected_value() -> None:
    with pytest.raises(MalformedOptionError) as exc_info:
        parse_options("--my-flag=oops", _FakeFlagIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "unexpected_value"
    assert payload["value"] == "--my-flag"


def test_flag_option_alone_yields_true() -> None:
    assert parse_options("--my-flag", _FakeFlagIntegration) == {"my_flag": True}


# ---------- FR-021 — required absent ----------


class _FakeRequiredIntegration(SkillsIntegration):
    key: ClassVar[str] = "fake-required"
    default_skills_dir: ClassVar[str] = ".fake/skills"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(flag="--needed", type="string", required=True),
        ]


def test_required_flag_supplied_succeeds() -> None:
    assert parse_options("--needed val", _FakeRequiredIntegration) == {"needed": "val"}


def test_required_flag_absent_with_other_input_raises_missing_required() -> None:
    """FR-021 — when input is non-empty but required flag is absent, MUST raise.

    Also a bug-guard: simply having SOME flag does not satisfy `required`.
    """

    class FakeMix(SkillsIntegration):
        key: ClassVar[str] = "fake-mix"
        default_skills_dir: ClassVar[str] = ".fake/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            return [
                IntegrationOption(flag="--needed", type="string", required=True),
                IntegrationOption(flag="--opt", type="string", required=False),
            ]

    with pytest.raises(MalformedOptionError) as exc_info:
        parse_options("--opt x", FakeMix)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "missing_required"
    assert payload["value"] == "--needed"


# ---------- FR-020 vs FR-021 precedence (R6) ----------


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_empty_input_short_circuits_even_with_required(raw: str | None) -> None:
    """FR-020 wins over FR-021 when the user supplied no options at all."""

    assert parse_options(raw, _FakeRequiredIntegration) == {}


# ---------- R8 — declared defaults are applied for omitted opts ----------


class _FakeWithDefaultIntegration(SkillsIntegration):
    """Stub declaring one optional string opt with `default='all'`."""

    key: ClassVar[str] = "fake-with-default"
    default_skills_dir: ClassVar[str] = ".fake/skills"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [IntegrationOption(flag="--scope", type="string", default="all")]


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_default_applied_on_empty_input(raw: str | None) -> None:
    """R8 — declared `default` is applied even when `raw` is empty."""

    assert parse_options(raw, _FakeWithDefaultIntegration) == {"scope": "all"}


def test_default_not_overridden_when_user_supplies_value() -> None:
    """R8 — user-supplied value takes precedence over the declared default."""

    assert parse_options("--scope project", _FakeWithDefaultIntegration) == {"scope": "project"}


def test_default_satisfies_required_when_user_omits_flag() -> None:
    """R8 — `required=True, default='x'` is satisfied by the default."""

    class FakeRequiredWithDefault(SkillsIntegration):
        key: ClassVar[str] = "fake-req-default"
        default_skills_dir: ClassVar[str] = ".fake/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            return [
                IntegrationOption(flag="--scope", type="string", required=True, default="all"),
                IntegrationOption(flag="--opt", type="string", required=False),
            ]

    # Non-empty input without --scope; the default fills it and
    # missing_required is NOT raised.
    assert parse_options("--opt x", FakeRequiredWithDefault) == {
        "scope": "all",
        "opt": "x",
    }


# ---------- FR-015 — programming-error guards ----------


def test_invalid_flag_prefix_in_descriptor_raises_invalid_declaration() -> None:
    class BadFlagIntegration(SkillsIntegration):
        key: ClassVar[str] = "bad-flag"
        default_skills_dir: ClassVar[str] = ".bad/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            # Missing the `--` prefix.
            return [IntegrationOption(flag="skills-dir", type="string")]

    with pytest.raises(InvalidOptionDeclarationError) as exc_info:
        parse_options("--anything x", BadFlagIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "bad_flag_prefix"
    assert payload["value"] == "skills-dir"


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_invalid_descriptor_raises_even_on_empty_input(raw: str | None) -> None:
    """R9 — FR-015 programming-error guards fire BEFORE the FR-020 empty
    short-circuit, so a broken `options()` declaration surfaces on the first
    call regardless of what the user supplied via `--integration-options`.
    """

    class BadFlagIntegration(SkillsIntegration):
        key: ClassVar[str] = "bad-flag-r9"
        default_skills_dir: ClassVar[str] = ".bad/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            return [IntegrationOption(flag="skills-dir", type="string")]

    with pytest.raises(InvalidOptionDeclarationError) as exc_info:
        parse_options(raw, BadFlagIntegration)
    assert exc_info.value.to_dict()["rule"] == "bad_flag_prefix"


def test_colliding_identifiers_in_descriptor_raises_invalid_declaration() -> None:
    """R15 — `--skills-dir` and `--skills_dir` both normalize to
    `skills_dir`; the parser would silently last-wins. Detect at
    declaration time so the integration author fixes the spelling.
    """

    class CollidingIntegration(SkillsIntegration):
        key: ClassVar[str] = "colliding"
        default_skills_dir: ClassVar[str] = ".coll/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            return [
                IntegrationOption(flag="--skills-dir", type="string"),
                IntegrationOption(flag="--skills_dir", type="string"),
            ]

    with pytest.raises(InvalidOptionDeclarationError) as exc_info:
        parse_options(None, CollidingIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "colliding_identifiers"
    assert "skills_dir" in str(payload["value"])
    assert "--skills-dir" in str(payload["value"])
    assert "--skills_dir" in str(payload["value"])


def test_duplicate_flag_declaration_raises_invalid_declaration() -> None:
    """R14 — two IntegrationOption entries with the same flag in one
    integration's options() is a programming error, not silent last-wins.
    """

    class DupFlagIntegration(SkillsIntegration):
        key: ClassVar[str] = "dup-flag"
        default_skills_dir: ClassVar[str] = ".dup/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            return [
                IntegrationOption(flag="--foo", type="string", required=True),
                IntegrationOption(flag="--foo", type="string", required=False),
            ]

    with pytest.raises(InvalidOptionDeclarationError) as exc_info:
        parse_options("--foo x", DupFlagIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "duplicate_flag"
    assert payload["value"] == "--foo"


def test_invalid_type_in_descriptor_raises_invalid_declaration() -> None:
    class BadTypeIntegration(SkillsIntegration):
        key: ClassVar[str] = "bad-type"
        default_skills_dir: ClassVar[str] = ".bad/skills"

        @classmethod
        def options(cls) -> list[IntegrationOption]:
            # mypy correctly flags 'weird' — we deliberately bypass for the test.
            return [IntegrationOption(flag="--x", type="weird")]  # type: ignore[arg-type]

    with pytest.raises(InvalidOptionDeclarationError) as exc_info:
        parse_options("--x 1", BadTypeIntegration)
    payload = exc_info.value.to_dict()
    assert payload["rule"] == "bad_type"
    assert payload["value"] == "weird"


# ---------- IntegrationOption descriptor itself ----------


def test_integration_option_is_frozen() -> None:
    opt = IntegrationOption(flag="--x", type="string")
    with pytest.raises(dataclasses.FrozenInstanceError):
        opt.flag = "--y"  # type: ignore[misc]


def test_integration_option_construction_with_bad_prefix_does_not_raise() -> None:
    """Per data-model: construction is permissive; the parser is the gate."""

    opt = IntegrationOption(flag="skills-dir", type="string")
    assert opt.flag == "skills-dir"
