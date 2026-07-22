#!/usr/bin/env bash
# Daily GemRate fetch (KST). Install to /usr/local/bin/pokepop-gemrate or run from repo.
set -euo pipefail

ENV_FILE="${POKEPOP_ENV:-/etc/pokepop-gemrate.env}"
if [[ -f "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
fi

INSTALL_DIR="${INSTALL_DIR:-/opt/pokepop}"
SLEEP_SEC="${GEMRATE_SLEEP_SEC:-60}"
LOG_DIR="${LOG_DIR:-/var/log/pokepop}"
GIT_PUSH="${GIT_PUSH:-1}"

mkdir -p "${LOG_DIR}"
LOG="${LOG_DIR}/gemrate-$(date +%Y%m%d).log"
exec >>"${LOG}" 2>&1

echo "=== $(date -Iseconds) pokepop-gemrate start ==="

cd "${INSTALL_DIR}"
if [[ ! -d .git ]]; then
  echo "ERROR: not a git repo: ${INSTALL_DIR}"
  exit 1
fi

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export GIT_TERMINAL_PROMPT=0
git fetch origin
BRANCH="$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')"
BRANCH="${BRANCH:-main}"
git reset --hard "origin/${BRANCH}"

python pokemon-pop/scripts/fetch_gemrate.py --sleep "${SLEEP_SEC}"
FETCH_EXIT=$?
if [[ "${FETCH_EXIT}" -ne 0 ]]; then
  echo "ERROR: fetch_gemrate exited ${FETCH_EXIT}"
  exit "${FETCH_EXIT}"
fi

if [[ "${GIT_PUSH}" != "1" ]]; then
  echo "GIT_PUSH=0, skip commit"
  exit 0
fi

git add \
  pokemon-pop/data/gemrate \
  pokemon-pop/data/live/pop-price.json \
  pokemon-pop/data/live/last-run.json \
  pokemon-pop/data/data.js

if git diff --staged --quiet; then
  echo "No changes to commit."
  exit 0
fi

git -c user.name="${GIT_AUTHOR_NAME:-pokepop-vps}" \
    -c user.email="${GIT_AUTHOR_EMAIL:-pokepop-vps@users.noreply.github.com}" \
    commit -m "chore(pokepop): daily GemRate PSA (Hetzner VPS) $(date +%Y-%m-%d)"

git push origin HEAD
echo "=== $(date -Iseconds) pokepop-gemrate done ==="
