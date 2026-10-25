#!/usr/bin/env bash
# GitHub CLI bootstrap for users whose GitHub app lacks new-repository creation.
# Requires a locally authenticated GitHub CLI with repository creation permission.
set -euo pipefail
cd "$(dirname "$0")/.."
repo="${ALGA_TWIN_REPO:-ysmhla/alga-twin}"
if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required: https://cli.github.com/" >&2
  exit 2
fi
gh auth status >/dev/null || { echo "Run: gh auth login" >&2; exit 2; }
if gh repo view "$repo" >/dev/null 2>&1; then
  echo "Repository $repo already exists. Nothing was overwritten." >&2
  exit 2
fi
if [ ! -d .git ]; then
  git init -b main
  git add .
  git -c user.name='AlgaTwin Contributors' -c user.email='alga-twin@users.noreply.github.com' commit -m 'feat: AlgaTwin scientific simulator v0.2.0'
fi
gh repo create "$repo" --public --source=. --remote=origin --push
echo "Published https://github.com/$repo"
