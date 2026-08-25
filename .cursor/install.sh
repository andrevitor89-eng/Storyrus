#!/usr/bin/env bash
# Idempotent dependency setup for the Storyrus (FortesHub) monorepo.
# Runs after the repository is checked out. Prepares the FastAPI backend
# (Python venv) and the Vite/React web app (npm), plus the Playwright
# browser used by the e2e suite. Safe to run repeatedly.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# The default image ships Python 3.12 but not the venv/ensurepip package.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv >/dev/null
fi

# ---- Backend (FastAPI) ----
cd "$repo_root/backend"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -e ".[dev]"
deactivate

# ---- Frontend (Vite + React) ----
cd "$repo_root/apps/web"
npm ci
# Chromium for the Playwright e2e suite (best-effort: e2e is optional in dev).
npx --yes playwright install --with-deps chromium || \
  npx --yes playwright install chromium || \
  echo "[install] playwright chromium install skipped (e2e browser unavailable)"

echo "[install] done"
