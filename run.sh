#!/usr/bin/env bash
# One command: download data, compute embeddings, write results/.
set -euo pipefail
cd "$(dirname "$0")"
command -v git >/dev/null || { echo "Needs git."; exit 1; }
command -v uv >/dev/null || { echo "Needs uv. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
uv run --locked python -m voicecheck.data
uv run --locked python -m voicecheck.embed
uv run --locked python -m voicecheck.evaluate
echo "Done. See results/summary.md"
