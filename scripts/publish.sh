#!/usr/bin/env bash
#
# publish.sh — build and publish bookwright-cli with `uv`, loading the PyPI
# token from ~/.pypirc (which `uv publish` does not read on its own).
#
# Usage:
#   scripts/publish.sh            # build + publish to PyPI    ([pypi] section)
#   scripts/publish.sh --test     # build + publish to TestPyPI ([testpypi] section)
#   scripts/publish.sh --no-build # skip `uv build`, publish existing dist/
#
set -euo pipefail

REPO="pypi"
PUBLISH_URL=""
DO_BUILD=1

for arg in "$@"; do
  case "$arg" in
    --test)     REPO="testpypi"; PUBLISH_URL="https://test.pypi.org/legacy/" ;;
    --no-build) DO_BUILD=0 ;;
    -h|--help)  grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

PYPIRC="${HOME}/.pypirc"
[ -f "$PYPIRC" ] || { echo "error: $PYPIRC not found" >&2; exit 1; }

# Pull the token for the chosen index out of ~/.pypirc via configparser (robust
# to indentation / key order) and export it as UV_PUBLISH_TOKEN. uv implies the
# username "__token__" from a token, so do NOT also pass a username — uv rejects
# --username together with --token.
UV_PUBLISH_TOKEN="$(
  REPO="$REPO" python3 - "$PYPIRC" <<'PY'
import configparser, os, sys
cfg = configparser.ConfigParser()
cfg.read(sys.argv[1])
section = os.environ["REPO"]
if not cfg.has_section(section):
    sys.exit(f"error: [{section}] section missing in {sys.argv[1]}")
token = cfg.get(section, "password", fallback="").strip()
if not token.startswith("pypi-"):
    sys.exit(f"error: [{section}] password is not a 'pypi-' token")
print(token)
PY
)"
export UV_PUBLISH_TOKEN

echo ">> target index: ${REPO}${PUBLISH_URL:+ ($PUBLISH_URL)}"
echo ">> token:         ${UV_PUBLISH_TOKEN:0:9}…[hidden]"

if [ "$DO_BUILD" -eq 1 ]; then
  echo ">> building artifacts (rm -rf dist && uv build)"
  rm -rf dist
  uv build
fi

echo ">> publishing"
if [ -n "$PUBLISH_URL" ]; then
  uv publish --publish-url "$PUBLISH_URL"
else
  uv publish
fi

echo ">> done."
